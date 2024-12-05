import asyncio
import json
import threading
import time
import traceback
import uuid
from datetime import datetime
from random import sample
from typing import cast, Dict, Optional

from aioredis import Redis
from communex.client import CommuneClient  # type: ignore
from communex.errors import NetworkTimeoutError
from communex.misc import get_map_modules
from communex.module.client import ModuleClient  # type: ignore
from communex.module.module import Module  # type: ignore
from communex.types import Ss58Address  # type: ignore
from loguru import logger
from substrateinterface import Keypair  # type: ignore
from ._config import ValidatorSettings, load_base_weights

from .database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from .database.models.challenge_money_flow import ChallengeMoneyFlowManager
from src.subnet.encryption import generate_hash
from .helpers import raise_exception_if_not_registered, get_ip_port, cut_to_max_allowed_weights
from .weights_storage import WeightsStorage
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager
from src.subnet.protocol import Challenge, ChallengesResponse, ChallengeMinerResponse, Discovery, \
    MODEL_KIND_BALANCE_TRACKING
from .. import VERSION


class Validator(Module):

    def __init__(
            self,
            key: Keypair,
            netuid: int,
            client: CommuneClient,
            weights_storage: WeightsStorage,
            miner_discovery_manager: MinerDiscoveryManager,
            challenge_money_flow_manager: ChallengeMoneyFlowManager,
            challenge_balance_tracking_manager: ChallengeBalanceTrackingManager,
            miner_receipt_manager: MinerReceiptManager,
            redis_client: Redis,
            query_timeout: int = 60,
            challenge_timeout: int = 60,

    ) -> None:
        super().__init__()

        self.miner_receipt_manager = miner_receipt_manager
        self.client = client
        self.key = key
        self.netuid = netuid
        self.challenge_timeout = challenge_timeout
        self.query_timeout = query_timeout
        self.weights_storage = weights_storage
        self.miner_discovery_manager = miner_discovery_manager
        self.terminate_event = threading.Event()
        self.challenge_money_flow_manager = challenge_money_flow_manager
        self.challenge_balance_tracking_manager = challenge_balance_tracking_manager
        self.redis_client = redis_client

    @staticmethod
    def get_addresses(client: CommuneClient, netuid: int) -> dict[int, str]:
        modules_adresses = client.query_map_address(netuid)
        for id, addr in modules_adresses.items():
            if addr.startswith('None'):
                port = addr.split(':')[1]
                modules_adresses[id] = f'0.0.0.0:{port}'
        logger.debug(f"Got modules addresses", modules_adresses=modules_adresses)
        return modules_adresses

    async def _challenge_miner(self, miner_info):
        start_time = time.time()
        try:
            connection, miner_metadata = miner_info
            module_ip, module_port = connection
            miner_key = miner_metadata['key']
            client = ModuleClient(module_ip, int(module_port), self.key)

            logger.info(f"Challenging miner", miner_key=miner_key)

            # Discovery Phase
            discovery = await self._get_discovery(client, miner_key)
            if not discovery:
                return None

            logger.debug(f"Got discovery for miner", miner_key=miner_key)

            # Challenge Phase
            challenge_response = await self._perform_challenges(client, miner_key, discovery)
            if not challenge_response:
                return None

            return ChallengeMinerResponse(
                version=discovery.version,
                graph_db=discovery.graph_db,
                network=discovery.network,
                money_flow_challenge_actual=challenge_response.money_flow_challenge_actual,
                money_flow_challenge_expected=challenge_response.money_flow_challenge_expected,
                balance_tracking_challenge_actual=challenge_response.balance_tracking_challenge_actual,
                balance_tracking_challenge_expected=challenge_response.balance_tracking_challenge_expected,
            )
        except Exception as e:
            logger.error(f"Failed to challenge miner", error=e, miner_key=miner_key)
            return None
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Execution time for challenge_miner", execution_time=execution_time, miner_key=miner_key)

    async def _get_discovery(self, client, miner_key) -> Discovery:
        try:
            discovery = await client.call(
                "discovery",
                miner_key,
                {"validator_version": str(VERSION), "validator_key": self.key.ss58_address},
                timeout=self.challenge_timeout,
            )

            return Discovery(**discovery)
        except Exception as e:
            logger.info(f"Miner failed to get discovery", miner_key=miner_key, error=e)
            return None

    async def _perform_challenges(self, client, miner_key, discovery) -> ChallengesResponse | None:

        async def execute_money_flow_challenge(money_flow_challenge):
            money_flow_challenge_actual = "0x"
            try:
                money_flow_challenge = Challenge.model_validate_json(money_flow_challenge)
                money_flow_challenge = await client.call(
                    "challenge",
                    miner_key,
                    {"challenge": money_flow_challenge.model_dump(), "validator_key": self.key.ss58_address},
                    timeout=self.challenge_timeout,
                )

                if money_flow_challenge is not None:
                    money_flow_challenge = Challenge(**money_flow_challenge)
                    money_flow_challenge_actual = money_flow_challenge.output['tx_id']
                    logger.debug(f"Money flow challenge result", money_flow_challenge_output=money_flow_challenge.output, miner_key=miner_key)
                return money_flow_challenge_actual

            except NetworkTimeoutError:
                logger.error(f"Miner failed to perform challenges - timeout", miner_key=miner_key)
            except Exception as e:
                logger.error(f"Miner failed to perform challenges", error=e, miner_key=miner_key, traceback=traceback.format_exc())
            finally:
                return money_flow_challenge_actual

        async def execute_balance_tracking_challenge(balance_tracking_challenge):
            balance_tracking_challenge_actual = 0
            try:
                balance_tracking_challenge = Challenge.model_validate_json(balance_tracking_challenge)
                balance_tracking_challenge = await client.call(
                    "challenge",
                    miner_key,
                    {"challenge": balance_tracking_challenge.model_dump(), "validator_key": self.key.ss58_address},
                    timeout=self.challenge_timeout,
                )

                if balance_tracking_challenge is not None:
                    balance_tracking_challenge = Challenge(**balance_tracking_challenge)
                    balance_tracking_challenge_actual = balance_tracking_challenge.output['balance']
                    logger.debug(f"Balance tracking challenge result", balance_tracking_challenge_output=balance_tracking_challenge.output, miner_key=miner_key)
            except NetworkTimeoutError:
                logger.error(f"Miner failed to perform challenges - timeout", miner_key=miner_key)
            except Exception as e:
                logger.error(f"Miner failed to perform challenges", error=e, miner_key=miner_key, traceback=traceback.format_exc())
            finally:
                return balance_tracking_challenge_actual

        try:
            money_flow_challenge, tx_id = await self.challenge_money_flow_manager.get_random_challenge(discovery.network)
            if money_flow_challenge is None:
                logger.warning(f"Failed to get money flow challenge", miner_key=miner_key)
                return None
            money_flow_challenge_actual = await execute_money_flow_challenge(money_flow_challenge)

            balance_tracking_challenge, balance_tracking_expected_response = await self.challenge_balance_tracking_manager.get_random_challenge(discovery.network)
            if balance_tracking_challenge is None:
                logger.warning(f"Failed to get balance tracking challenge", miner_key=miner_key)
                return None
            balance_tracking_challenge_actual = await execute_balance_tracking_challenge(balance_tracking_challenge)

            return ChallengesResponse(
                money_flow_challenge_actual=money_flow_challenge_actual,
                money_flow_challenge_expected=tx_id,
                balance_tracking_challenge_actual=balance_tracking_challenge_actual,
                balance_tracking_challenge_expected=balance_tracking_expected_response,
            )
        except NetworkTimeoutError as e:
            logger.error(f"Miner failed to perform challenges - timeout", error=e, miner_key=miner_key)
            return None
        except Exception as e:
            logger.error(f"Miner failed to perform challenges", error=e, miner_key=miner_key, traceback=traceback.format_exc())
            return None

    @staticmethod
    def _score_miner(response: ChallengeMinerResponse, receipt_miner_multiplier: float) -> float:

        if not response:
            logger.debug(f"Skipping empty response")
            return 0

        failed_challenges = response.get_failed_challenges()
        if failed_challenges > 0:
            if failed_challenges == 2:
                return 0
            else:
                return 0.15

        score = 0.3

        multiplier = min(1.0, receipt_miner_multiplier)
        score = score + (0.7 * multiplier)

        # TODO: fraud detection: if given miner loves too much certain valdiator, it's a fraud

        return score

    @staticmethod
    def adjust_network_weights_with_min_threshold(organic_prompts, min_threshold_ratio=5):
        base_weights = load_base_weights()
        total_base_weight = sum(base_weights.values())
        normalized_base_weights = {k: (v / total_base_weight) * 100 for k, v in base_weights.items()}
        num_networks = len(base_weights)
        min_threshold = 100 / min_threshold_ratio  # Minimum threshold percentage
        total_prompts = sum(organic_prompts.values())

        adjusted_weights = {}

        if total_prompts == 0:
            adjusted_weights = normalized_base_weights.copy()
        else:
            for network in normalized_base_weights.keys():
                organic_ratio = organic_prompts.get(network, 0) / total_prompts
                adjusted_weight = normalized_base_weights[network] * organic_ratio

                if adjusted_weight < min_threshold:
                    adjusted_weights[network] = min_threshold
                else:
                    adjusted_weights[network] = adjusted_weight

            total_adjusted_weight = sum(adjusted_weights.values())

            if total_adjusted_weight > 100:
                weight_above_min = total_adjusted_weight - (min_threshold * num_networks)
                if weight_above_min > 0:
                    scale_factor = (100 - (min_threshold * num_networks)) / weight_above_min
                    for network in adjusted_weights.keys():
                        if adjusted_weights[network] > min_threshold:
                            adjusted_weights[network] = min_threshold + (
                                        adjusted_weights[network] - min_threshold) * scale_factor
                else:
                    for network in adjusted_weights.keys():
                        adjusted_weights[network] = min_threshold

        return adjusted_weights

    async def validate_step(self, netuid: int, settings: ValidatorSettings) -> None:

        score_dict: dict[int, float] = {}
        miners_module_info = {}

        modules = cast(dict[str, Dict], get_map_modules(self.client, netuid=netuid, include_balances=False))
        modules_addresses = self.get_addresses(self.client, netuid)
        ip_ports = get_ip_port(modules_addresses)

        raise_exception_if_not_registered(self.key, modules)

        for key in modules.keys():
            module_meta_data = modules[key]
            uid = module_meta_data['uid']
            if uid not in ip_ports:
                continue
            module_addr = ip_ports[uid]
            miners_module_info[uid] = (module_addr, modules[key])

        logger.info(f"Found miners", miners_module_info=miners_module_info.keys())

        for _, miner_metadata in miners_module_info.values():
            await self.miner_discovery_manager.update_miner_rank(miner_metadata['key'], miner_metadata['emission'])

        challenge_tasks = []
        for uid, miner_info in miners_module_info.items():
            challenge_tasks.append(self._challenge_miner(miner_info))

        responses: tuple[ChallengeMinerResponse] = await asyncio.gather(*challenge_tasks)

        for uid, miner_info, response in zip(miners_module_info.keys(), miners_module_info.values(), responses):
            if not response:
                score_dict[uid] = 0
                continue

            if isinstance(response, ChallengeMinerResponse):
                network = response.network
                version = response.version
                graph_db = response.graph_db
                connection, miner_metadata = miner_info
                miner_address, miner_ip_port = connection
                miner_key = miner_metadata['key']

                organic_usage = await self.miner_receipt_manager.get_receipts_count_by_networks()
                adjusted_weights = self.adjust_network_weights_with_min_threshold(organic_usage, min_threshold_ratio=5)
                logger.debug(f"Adjusted weights", adjusted_weights=adjusted_weights, miner_key=miner_key)

                receipt_miner_multiplier_result = await self.miner_receipt_manager.get_receipt_miner_multiplier(network, miner_key)
                if not receipt_miner_multiplier_result:
                    receipt_miner_multiplier = 1
                else:
                    receipt_miner_multiplier = receipt_miner_multiplier_result[0]['multiplier']

                score = self._score_miner(response, receipt_miner_multiplier)

                weighted_score = 0
                total_weight = sum(adjusted_weights.values())
                weight = adjusted_weights[response.network]
                network_influence = weight / total_weight
                weighted_score += score * network_influence

                assert weighted_score <= 1
                score_dict[uid] = weighted_score

                await self.miner_discovery_manager.store_miner_metadata(uid, miner_key, miner_address, miner_ip_port, network, version, graph_db)
                await self.miner_discovery_manager.update_miner_challenges(miner_key, response.get_failed_challenges(), 2)

        if not score_dict:
            logger.info("No miner managed to give a valid answer")
            return None

        try:
            self.set_weights(settings, score_dict, self.netuid, self.client, self.key)
        except Exception as e:
            logger.error(f"Failed to set weights", error=e)

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

        logger.debug(f"Setting weights for scores", score_dict=score_dict)
        score_sum = sum(score_dict.values())

        for uid, score in score_dict.items():
            if score_sum == 0:
                weight = 0
                weighted_scores[uid] = weight
            else:
                weight = int(score * 1000 / score_sum)
                weighted_scores[uid] = weight

        weighted_scores = {k: v for k, v in weighted_scores.items() if k in score_dict}

        self.weights_storage.store(weighted_scores)

        uids = list(weighted_scores.keys())
        weights = list(weighted_scores.values())

        if len(weighted_scores) > 0:
            client.vote(key=key, uids=uids, weights=weights, netuid=netuid)

        logger.info("Set weights", action="set_weight", timestamp=datetime.utcnow().isoformat(), weighted_scores=weighted_scores)

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

    @staticmethod
    def format_query_string(query_string: str):
        import re
        cleaned = query_string.replace('\n', ' ').replace('\t', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        return cleaned

    async def query_miner(self, network: str, model_kind: str, query, miner_key: Optional[str]) -> dict:
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        query = self.format_query_string(query)
        query_hash = generate_hash(query)

        # Single miner case
        if miner_key:
            miner = await self.miner_discovery_manager.get_miner_by_key(miner_key, network)
            if not miner:
                return {
                    "request_id": request_id,
                    "timestamp": timestamp,
                    "miner_keys": None,
                    "network": network,
                    "model_kind": model_kind,
                    "response": []
                }

            response = await self._query_miner(miner, model_kind, query)
            if response:
                return {
                    "request_id": request_id,
                    "timestamp": timestamp,
                    "miner_keys": [miner_key],
                    "network": network,
                    "model_kind": model_kind,
                    **response

                }
            return {
                "request_id": request_id,
                "timestamp": timestamp,
                "miner_keys": [miner_key],
                "network": network,
                "model_kind": model_kind,
                "response": None
            }

        # Multiple miners case
        select_count = 3
        sample_size = 16

        miners = await self.miner_discovery_manager.get_miners_by_network(network)
        if 3 > len(miners) > 0:
            top_miners = miners
        if len(miners) == 0:
            return {
                "request_id": request_id,
                "timestamp": timestamp,
                "miner_keys": [],
                "network": network,
                "model_kind": model_kind,
                "response": None
            }
        else:
            top_miners = miners if len(miners) <= select_count else sample(miners, select_count)

        #WE KEEP IT HERE FOR DEBUGGING PURPOSES
        ## 5DvXP65LQe5SfePQ2Bge6RmxV3pWehNmv7nt1fEvMFeHifkU","5G4mWAWB8ZKo4sYfu69Fpeg6aGkWE8ZzeXXTjUT8G4TPFaTE","5HpXG24woTs38cpykk8EsjvuCFaz2hM3vu9fdnMEXLGaq3pt
        #m1 = top_miners[0]
        #m1.update({'miner_key': '5GE8x7wN7hpyEZPWsE9wRpqZ9fyX367aDEzGCfSkqsP6GHqV'})
        #m1.update({'miner_address': '127.0.0.1'})
        #m1.update({'miner_ip_port': 9962})

        #m2 = top_miners[0]
        #m2.update({'miner_key': '5DvXP65LQe5SfePQ2Bge6RmxV3pWehNmv7nt1fEvMFeHifkU'})
        #m2.update({'miner_address': '66.248.206.106'})
        #m2.update({'miner_ip_port': 32214})

        #top_miners = [m1, m2]  # For now, we only query the top miner
        #top_miners = top_miners
        #"""

        responses = {}

        query_tasks = {
            asyncio.create_task(self._query_miner(miner, model_kind, query)): (miner, time.time())
            for miner in top_miners
        }

        try:
            pending = set(query_tasks.keys())
            start_time = time.time()

            while pending:
                if time.time() - start_time > self.query_timeout:
                    break

                # Wait for the next task to complete with timeout
                done, pending = await asyncio.wait(
                    pending,
                    timeout=max(0.0, self.query_timeout - (time.time() - start_time)),
                    return_when=asyncio.FIRST_COMPLETED
                )

                if not done:  # Timeout reached
                    break

                # Process completed tasks
                for completed_task in done:
                    try:
                        response = await completed_task
                        current_miner, start_time = query_tasks[completed_task]
                        response_time = round(time.time() - start_time, 3)

                        if not response:
                            continue

                        result_hash = response['response']['result_hash']
                        result_hash_signature = response['response']["result_hash_signature"]

                        miner_key = current_miner['miner_key']
                        miner_key_pair = Keypair(ss58_address=miner_key)
                        result_hash_signature_bytes = bytes.fromhex(result_hash_signature)

                        if not miner_key_pair.verify(result_hash.encode('utf-8'), signature=result_hash_signature_bytes):
                            logger.warning(f"Invalid result hash signature", miner_key=miner_key, validator_key=self.key.ss58_address)
                            continue

                        # Add to or update our response tracking
                        if result_hash in responses:
                            # We found a match!
                            existing_response, existing_miners = responses[result_hash]
                            existing_miners.append(current_miner)

                            # Store receipts for both miners
                            first_miner = existing_miners[0]

                            receipt = {
                                "validator_key": self.key.ss58_address,
                                "request_id": request_id,
                                "miner_key": first_miner['miner_key'],
                                "model_kind": model_kind,
                                "network": network,
                                "query": query,
                                "query_hash": query_hash,
                                "response_time": response_time,
                                "timestamp": timestamp.isoformat(),
                                "result_hash": result_hash,
                                "result_hash_signature": result_hash_signature
                            }

                            await self.redis_client.lpush('receipts', json.dumps(receipt))

                            # Cancel remaining tasks
                            for task in pending:
                                task.cancel()

                            return {
                                "request_id": request_id,
                                "timestamp": timestamp,
                                "miner_keys": [miner['miner_key'] for miner in top_miners],
                                "network": network,
                                "model_kind": model_kind,
                                **existing_response
                            }
                        else:
                            # First time seeing this response, store it
                            responses[result_hash] = (response, [current_miner])
                    except Exception as e:
                        logger.error(f"Error querying miner", error=e)
                        continue

            # No valid responses at all, returning empty response
            return {
                "request_id": request_id,
                "timestamp": timestamp,
                "miner_keys": [],
                "network": network,
                "model_kind": model_kind,
                "response": None,
            }

        finally:
            for task in query_tasks.keys():
                if not task.done():
                    task.cancel()

    async def _query_miner(self, miner, model_kind, query):
        miner_key = miner['miner_key']
        miner_network = miner['network']
        module_ip = miner['miner_address']
        module_port = int(miner['miner_ip_port'])
        module_client = ModuleClient(module_ip, module_port, self.key)
        try:
            query_result = await module_client.call(
                "query",
                miner_key,
                {"model_kind": model_kind, "query": query, "validator_key": self.key.ss58_address},
                timeout=self.query_timeout,
            )
            if not query_result:
                return None

            return self.unpack_response(query_result, model_kind)
        except Exception as e:
            logger.warning(f"Failed to query miner", error=e, miner_key=miner_key)
            return None

    @staticmethod
    def unpack_response(response, model_kind):
        if model_kind == MODEL_KIND_BALANCE_TRACKING:
            response['result'] = response["result"][0]['response_json']
            return {
                "response": response
            }
        elif model_kind == MONEY_FLOW_MODEL_TYPE:
            if isinstance(response, dict):
                response['result'] = {
                    "data": response['result']
                }
                return {
                   "response": response
                }
            else:
                return {
                    "response": response
                }

        raise ValueError(f"Invalid model type: {model_kind}")
