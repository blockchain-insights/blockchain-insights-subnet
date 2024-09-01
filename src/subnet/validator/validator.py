import asyncio
import json
import threading
import time
import uuid
from datetime import datetime
from random import sample, randint
from typing import cast, List, Dict

from communex.client import CommuneClient  # type: ignore
from communex.misc import get_map_modules
from communex.module.client import ModuleClient  # type: ignore
from communex.module.module import Module  # type: ignore
from communex.types import Ss58Address  # type: ignore
from pydantic import BaseModel
from substrateinterface import Keypair  # type: ignore
from ._config import ValidatorSettings
from loguru import logger

from .encryption import generate_hash
from .helpers import raise_exception_if_not_registered, get_ip_port, cut_to_max_allowed_weights
from .nodes.factory import NodeFactory
from .weights_storage import WeightsStorage
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipts import MinerReceiptManager, ReceiptMinerRank
from src.subnet.protocol.llm_engine import LlmQueryRequest, LlmMessage, Challenge, LlmMessageList, ChallengesResponse, \
    ChallengeMinerResponse, LlmMessageOutputList
from src.subnet.protocol.blockchain import Discovery
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager


class Validator(Module):

    def __init__(
            self,
            key: Keypair,
            netuid: int,
            client: CommuneClient,
            weights_storage: WeightsStorage,
            miner_discovery_manager: MinerDiscoveryManager,
            validation_prompt_manager: ValidationPromptManager,
            miner_receipt_manager: MinerReceiptManager,
            query_timeout: int = 60,
            llm_query_timeout: int = 60,
            challenge_timeout: int = 60,

    ) -> None:
        super().__init__()

        self.miner_receipt_manager = miner_receipt_manager
        self.client = client
        self.key = key
        self.netuid = netuid
        self.llm_query_timeout = llm_query_timeout
        self.challenge_timeout = challenge_timeout
        self.query_timeout = query_timeout
        self.weights_storage = weights_storage
        self.miner_discovery_manager = miner_discovery_manager
        self.terminate_event = threading.Event()
        self.validation_prompt_manager = validation_prompt_manager

    @staticmethod
    def get_addresses(client: CommuneClient, netuid: int) -> dict[int, str]:
        modules_adresses = client.query_map_address(netuid)
        for id, addr in modules_adresses.items():
            if addr.startswith('None'):
                port = addr.split(':')[1]
                modules_adresses[id] = f'0.0.0.0:{port}'
        return modules_adresses

    async def _challenge_miner(self, miner_info):
        start_time = time.time()
        try:
            connection, miner_metadata = miner_info
            module_ip, module_port = connection
            miner_key = miner_metadata['key']
            client = ModuleClient(module_ip, int(module_port), self.key)

            logger.info(f"Challenging miner {miner_key}")

            # Discovery Phase
            discovery = await self._get_discovery(client, miner_key)
            if not discovery:
                return None

            logger.debug(f"Got discovery for miner {miner_key}")

            # Challenge Phase
            node = NodeFactory.create_node(discovery.network)
            challenge_response = await self._perform_challenges(client, miner_key, discovery, node)
            if not challenge_response:
                return None

            # Prompt Phase
            random_validation_prompt = await self.validation_prompt_manager.get_random_prompt()
            if not random_validation_prompt:
                logger.error("Failed to get a random validation prompt")
                return None

            llm_message_list = LlmMessageList(messages=[LlmMessage(type=0, content=random_validation_prompt)])
            llm_query_result = await self._send_prompt(client, miner_key, llm_message_list)
            if not llm_query_result:
                return None

            prompt_cross_check_miner_keys = await self.miner_discovery_manager.get_miners_for_cross_check(discovery.network)
            prompt_cross_check_tasks = []
            for _miner_key in prompt_cross_check_miner_keys:
                prompt_cross_check_tasks.append(self._send_prompt(client, _miner_key, llm_message_list))

            prompt_result_cross_checks: LlmMessageOutputList = await asyncio.gather(*prompt_cross_check_tasks)

            return ChallengeMinerResponse(
                network=discovery.network,
                funds_flow_challenge_actual=challenge_response.funds_flow_challenge_actual,
                funds_flow_challenge_expected=challenge_response.funds_flow_challenge_expected,
                balance_tracking_challenge_actual=challenge_response.balance_tracking_challenge_actual,
                balance_tracking_challenge_expected=challenge_response.balance_tracking_challenge_expected,
                prompt_result_cross_checks=prompt_result_cross_checks,
                prompt_result=llm_query_result,
            )
        except Exception as e:
            logger.error(f"Failed to challenge miner {miner_key}, {e}")
            return None
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Execution time for challenge_miner {miner_key}: {execution_time} seconds")

    async def _get_discovery(self, client, miner_key) -> Discovery:
        try:
            discovery = await client.call(
                "discovery",
                miner_key,
                {},
                timeout=self.challenge_timeout,
            )

            return Discovery(**discovery)
        except Exception as e:
            logger.info(f"Miner {miner_key} failed to get discovery")
            return None

    async def _perform_challenges(self, client, miner_key, discovery, node) -> ChallengesResponse | None:
        try:
            last_block_height = node.get_current_block_height() - 6

            # Funds flow challenge
            funds_flow_challenge, tx_id = node.create_funds_flow_challenge(0, last_block_height)
            funds_flow_challenge = await client.call(
                "challenge",
                miner_key,
                {"challenge": funds_flow_challenge.dict()},
                timeout=self.challenge_timeout,
            )
            funds_flow_challenge = Challenge(**funds_flow_challenge)
            logger.debug(f"Funds flow challenge result for {miner_key}: {funds_flow_challenge.output}")

            # Balance tracking challenge
            random_balance_tracking_block = randint(1, 1000)  # this is for fast testing only, remove on production
            balance_tracking_challenge, balance_tracking_expected_response = node.create_balance_tracking_challenge(random_balance_tracking_block)
            balance_tracking_challenge = await client.call(
                "challenge",
                miner_key,
                {"challenge": balance_tracking_challenge.dict()},
                timeout=self.challenge_timeout,
            )
            balance_tracking_challenge = Challenge(**balance_tracking_challenge)
            logger.debug(f"Balance tracking challenge result for {miner_key}: {balance_tracking_challenge.output}")

            return ChallengesResponse(
                funds_flow_challenge_actual=funds_flow_challenge.output['tx_id'],
                funds_flow_challenge_expected=tx_id,
                balance_tracking_challenge_actual=balance_tracking_challenge.output['balance'],
                balance_tracking_challenge_expected=balance_tracking_expected_response,
            )
        except Exception as e:
            logger.error(f"Miner {miner_key} failed to perform challenges: {e}")
            return None

    async def _send_prompt(self, client, miner_key, llm_message_list) -> LlmMessageOutputList | None:
        try:
            llm_query_result = await client.call(
                "llm_query",
                miner_key,
                {"llm_messages_list": llm_message_list.model_dump()},
                timeout=self.llm_query_timeout,
            )
            if not llm_query_result:
                return None

            return LlmMessageOutputList(**llm_query_result)
        except Exception as e:
            logger.info(f"Miner {miner_key} failed to generate an answer")
            return None

    @staticmethod
    def _score_miner(response: ChallengeMinerResponse, receipt_miner_multiplier: float) -> float:
        if not response:
            logger.info(f"Miner didn't answer")
            return 0

        failed_challenges = response.get_failed_challenges()
        if failed_challenges > 0:
            if failed_challenges == 2:
                return 0
            else:
                return 0.15

        # all challenges are passed, setting base score to 0.36
        score = 0.3

        if response.prompt_result is None:
            return score

        if response.prompt_result_cross_checks is None:
            return score

        # TODO: implement prompt cross checks
        # max to +0.3

        multiplier = min(1.0, receipt_miner_multiplier)
        score += 0.4 * multiplier

        return score

    async def validate_step(self, netuid: int, settings: ValidatorSettings
                            ) -> None:

        score_dict: dict[int, float] = {}
        miners_module_info = {}

        modules = cast(dict[str, Dict], get_map_modules(self.client, netuid=netuid, include_balances=False))
        modules_addresses = self.get_addresses(self.client, netuid)
        ip_ports = get_ip_port(modules_addresses)

        raise_exception_if_not_registered(self.key, modules)

        for key in modules.keys():
            module_meta_data = modules[key]
            uid = module_meta_data['uid']
            stake = module_meta_data['stake']
            if stake > 100:
                logger.debug(f"Skipping module {uid} with stake {stake} as it probably is not a miner")
                continue
            if uid not in ip_ports:
                logger.debug(f"Skipping module {uid} as it doesn't have an IP address")
                continue
            module_addr = ip_ports[uid]
            miners_module_info[uid] = (module_addr, modules[key])

        logger.info(f"Found the following miners: {miners_module_info.keys()}")

        logger.debug("Updating miner ranks")
        for _, miner_metadata in miners_module_info.values(): # this is intentionally in this place
            await self.miner_discovery_manager.update_miner_rank(miner_metadata['key'], miner_metadata['emission'])

        challenge_tasks = []
        for uid, miner_info in miners_module_info.items():
            challenge_tasks.append(self._challenge_miner(miner_info))

        logger.debug(f"Challenging {len(challenge_tasks)} miners")
        responses: tuple[ChallengeMinerResponse] = await asyncio.gather(*challenge_tasks)
        logger.debug(f"Got responses from {len(responses)} miners")

        for uid, miner_info, response in zip(miners_module_info.keys(), miners_module_info.values(), responses):
            if not response:
                score_dict[uid] = 0
                continue

            if isinstance(response, ChallengeMinerResponse):
                network = response.network
                connection, miner_metadata = miner_info
                miner_address, miner_ip_port = connection
                miner_key = miner_metadata['key']
                receipt_miner_multiplier = await self.miner_receipt_manager.get_receipt_miner_multiplier(miner_key)
                score = self._score_miner(response, receipt_miner_multiplier)
                assert score <= 1
                score_dict[uid] = score

                await self.miner_discovery_manager.store_miner_metadata(uid, miner_key, miner_address, miner_ip_port, network)
                await self.miner_discovery_manager.update_miner_challenges(miner_key, response.get_failed_challenges(), 2)

        if not score_dict:
            logger.info("No miner managed to give a valid answer")
            return None

        try:
            self.set_weights(settings, score_dict, self.netuid, self.client, self.key)
        except Exception as e:
            logger.error(f"Failed to set weights: {e}")

    def set_weights(self,
                    settings: ValidatorSettings,
                    score_dict: dict[
                        int, float
                    ],
                    netuid: int,
                    client: CommuneClient,
                    key: Keypair,
                    ) -> None:

        score_dict = cut_to_max_allowed_weights(score_dict, settings.MAX_ALLOWED_WEIGHTS)
        self.weights_storage.setup()
        weighted_scores: dict[int, int] = self.weights_storage.read()

        scores = sum(score_dict.values())

        if scores == 0:
            logger.warning("No scores to distribute")
            return

        for uid, score in score_dict.items():
            weight = int(score * 1000 / scores)
            weighted_scores[uid] = weight

        # filter out 0 weights
        weighted_scores = {k: v for k, v in weighted_scores.items() if v != 0}

        self.weights_storage.store(weighted_scores)
        uids = list(weighted_scores.keys())
        weights = list(weighted_scores.values())

        # send the blockchain call
        client.vote(key=key, uids=uids, weights=weights, netuid=netuid)

    async def validation_loop(self, settings: ValidatorSettings) -> None:
        while not self.terminate_event.is_set():
            start_time = time.time()
            await self.validate_step(self.netuid, settings)
            if self.terminate_event.is_set():
                logger.info("Terminating validation loop")
                break

            elapsed = time.time() - start_time
            if elapsed < settings.ITERATION_INTERVAL:
                sleep_time = settings.ITERATION_INTERVAL - elapsed
                logger.info(f"Sleeping for {sleep_time}")
                self.terminate_event.wait(sleep_time)
                if self.terminate_event.is_set():
                    logger.info("Terminating validation loop")
                    break

    """ VALIDATOR API METHODS"""
    async def query_miner(self, request: LlmQueryRequest) -> dict:
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        prompt_dict = [message.model_dump() for message in request.prompt]
        prompt_hash = generate_hash(json.dumps(prompt_dict))

        if request.miner_key:
            miner = await self.miner_discovery_manager.get_miner_by_key(request.miner_key, request.network)
            if not miner:
                return {
                    "request_id": request_id,
                    "timestamp": timestamp,
                    "miner_keys": [],
                    "prompt_hash": prompt_hash,
                    "response": []}

            result = await self._query_miner(miner, request)

            await self.miner_receipt_manager.store_miner_receipt(request_id, request.miner_key, prompt_hash, timestamp)

            return {
                "request_id": request_id,
                "timestamp": timestamp,
                "miner_keys": [request.miner_key],
                "prompt_hash": prompt_hash,
                "response": result,
            }
        else:
            select_count = 3
            sample_size = 16
            miners = await self.miner_discovery_manager.get_miners_by_network(request.network)

            if len(miners) < 3:
                top_miners = miners
            else:
                top_miners = sample(miners[:sample_size], select_count)

            query_tasks = []
            for miner in top_miners:
                query_tasks.append(self._query_miner(miner, request.prompt))

            responses = await asyncio.gather(*query_tasks)

            for miner, response in zip(top_miners, responses):
                if response:
                    await self.miner_receipt_manager.store_miner_receipt(request_id, miner['miner_key'], prompt_hash, timestamp)

            return {
                "request_id": request_id,
                "timestamp": timestamp,
                "miner_keys": [miner['miner_key'] for miner in top_miners],
                "prompt_hash": prompt_hash,
                "response": responses,
            }

    async def _query_miner(self, miner, llm_message_list: LlmMessageList):
        miner_key = miner['miner_key']
        miner_network = miner['network']
        module_ip = miner['miner_address']
        module_port = int(miner['miner_ip_port'])
        module_client = ModuleClient(module_ip, module_port, self.key)
        try:
            llm_query_result = await module_client.call(
                "llm_query",
                miner_key,
                {"llm_messages_list": llm_message_list.model_dump()},
                timeout=self.llm_query_timeout,
            )
            if not llm_query_result:
                return None

            return LlmMessageOutputList(**llm_query_result)
        except Exception as e:
            logger.warning(f"Failed to query miner {miner_key}, {e}")
            return None
