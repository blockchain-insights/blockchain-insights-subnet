import asyncio
import json
import threading
import time
import uuid
from datetime import datetime
from random import sample
from typing import cast, Dict, Optional

from aioredis import Redis
from communex.client import CommuneClient  # type: ignore
from communex.misc import get_map_modules
from communex.module.client import ModuleClient  # type: ignore
from communex.module.module import Module  # type: ignore
from communex.types import Ss58Address  # type: ignore
from loguru import logger
from substrateinterface import Keypair  # type: ignore
from ._config import ValidatorSettings, load_base_weights
from src.subnet.encryption import generate_hash
from .helpers import raise_exception_if_not_registered, get_ip_port, cut_to_max_allowed_weights
from .nodes.factory import NodeFactory
from .nodes.random_block import select_block
from .weights_storage import WeightsStorage
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager
from src.subnet.protocol import Discovery, MODEL_KIND_BALANCE_TRACKING, MODEL_KIND_MONEY_FLOW, \
    MODEL_KIND_TRANSACTION_STREAM, NETWORK_BITCOIN, get_networks, NETWORK_COMMUNE
from .. import VERSION


class Validator(Module):

    def __init__(
            self,
            key: Keypair,
            netuid: int,
            client: CommuneClient,
            weights_storage: WeightsStorage,
            miner_discovery_manager: MinerDiscoveryManager,
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

    async def _get_discovery(self, client, miner_key) -> Optional[Discovery]:
        try:
            discovery_data = await client.call(
                "discovery",
                miner_key,
                {"validator_version": str(VERSION), "validator_key": self.key.ss58_address},
                timeout=self.challenge_timeout,
            )

            if not self._is_valid_discovery(discovery_data):
                logger.warning(
                    "Invalid discovery data received",
                    miner_key=miner_key,
                    discovery_data=discovery_data
                )
                return None

            return Discovery(**discovery_data)
        except Exception as e:
            logger.info(f"Miner failed to get discovery", miner_key=miner_key, error=e)
            return None

    def _is_valid_discovery(self, discovery: dict) -> bool:
        try:
            if not all(key in discovery for key in ['network', 'version']):
                return False

            valid_networks = get_networks()
            if discovery['network'] not in valid_networks:
                logger.warning(
                    f"Invalid network in discovery data. Got {discovery['network']}, "
                    f"expected one of {valid_networks}"
                )
                return False

            try:
                version = int(discovery['version'])
                if version <= 0:
                    logger.warning(f"Invalid version number: {version}. Must be greater than 0")
                    return False
            except (ValueError, TypeError):
                logger.warning(
                    f"Version must be a valid integer, got {discovery['version']}"
                )
                return False

            return True

        except Exception as e:
            logger.warning(f"Error validating discovery data: {e}")
            return False

    async def get_discovery(self, miner_info) -> Discovery:
        connection, miner_metadata = miner_info
        module_ip, module_port = connection
        miner_key = miner_metadata['key']
        client = ModuleClient(module_ip, int(module_port), self.key)
        return await self._get_discovery(client, miner_key)

    @staticmethod
    def _score_miner(miner_key: str, response: dict, receipt_miner_multiplier: float) -> float:

        money_flow_consensus_hash = response['model_kinds']['money_flow']['consensus']['hash']
        balance_tracking_consensus_hash = response['model_kinds']['balance_tracking']['consensus']['hash']
        transaction_stream_consensus_hash = response['model_kinds']['transaction_stream']['consensus']['hash']

        miner_money_flow_hash = None
        miner_balance_tracking_hash = None
        miner_transaction_stream_hash = None

        score = 0

        if miner_key in response['model_kinds']['money_flow']['miners']:
            miner_money_flow_hash = response['model_kinds']['money_flow']['miners'][miner_key]['hash']

        if miner_key in response['model_kinds']['balance_tracking']['miners']:
            miner_balance_tracking_hash = response['model_kinds']['balance_tracking']['miners'][miner_key]['hash']

        if miner_key in response['model_kinds']['transaction_stream']['miners']:
            miner_transaction_stream_hash = response['model_kinds']['transaction_stream']['miners'][miner_key]['hash']

        if miner_transaction_stream_hash is not None and transaction_stream_consensus_hash == miner_transaction_stream_hash:
            score = score + 0.1

        if miner_balance_tracking_hash is not None and balance_tracking_consensus_hash == miner_balance_tracking_hash:
            score = score + 0.1

        if miner_money_flow_hash is not None and money_flow_consensus_hash == miner_money_flow_hash:
            score = score + 0.1

        if score == 0:
            return 0

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

        validation_timestamp = datetime.utcnow()
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

        discovery_tasks = []
        for uid, miner_info in miners_module_info.items():
            discovery_tasks.append(self.get_discovery(miner_info))
        discovery_responses: list[Discovery] = await asyncio.gather(*discovery_tasks)

        for uid, miner_info, discovery_response in zip(miners_module_info.keys(), miners_module_info.values(), discovery_responses):
            try:
                miner_metadata = miner_info[1]
                miner_key = miner_metadata['key']
                miner_ip = miner_info[0][0]
                miner_port = miner_info[0][1]

                if discovery_response is None:
                    logger.warning(
                        "Skipping miner due to failed discovery",
                        uid=uid,
                        miner_key=miner_key,
                        miner_ip=miner_ip,
                        miner_port=miner_port
                    )
                    continue

                miner_network = discovery_response.network
                miner_version = discovery_response.version

                await self.miner_discovery_manager.store_miner_metadata(
                    uid=uid,
                    miner_key=miner_key,
                    miner_address=miner_ip,
                    miner_ip_port=miner_port,
                    network=miner_network,
                    version=miner_version,
                    timestamp=validation_timestamp)

            except Exception as e:
                logger.error(
                    "Error processing miner metadata",
                    uid=uid,
                    error=str(e)
                )

        # Updating miners rank from previous validation step
        for _, miner_metadata in miners_module_info.values():
            await self.miner_discovery_manager.update_miner_rank(miner_metadata['key'], miner_metadata['emission'])

        challenge_miners_tasks = {}
        for network in get_networks():
            challenge_miners_tasks[network] = self.challenge_miners(network)

        challenge_miners_responses = await asyncio.gather(*challenge_miners_tasks.values())
        challenge_miners_responses_grouped = {network: response for network, response in zip(challenge_miners_tasks.keys(), challenge_miners_responses)}

        for uid, miner_info, discovery_response in zip(miners_module_info.keys(), miners_module_info.values(), discovery_responses):
            if not discovery_response:
                score_dict[uid] = 0
                continue

            if isinstance(discovery_response, Discovery):
                network = discovery_response.network
                version = discovery_response.version
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

                score = self._score_miner(miner_key, challenge_miners_responses_grouped[network], receipt_miner_multiplier)

                weighted_score = 0
                total_weight = sum(adjusted_weights.values())
                weight = adjusted_weights[network]
                network_influence = weight / total_weight
                weighted_score += score * network_influence

                assert weighted_score <= 1
                score_dict[uid] = weighted_score

                #await self.miner_discovery_manager.store_miner_metadata(uid, miner_key, miner_address, miner_ip_port, network, version, graph_db)
                #await self.miner_discovery_manager.update_miner_challenges(miner_key, response.get_failed_challenges(), 2)

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

    @staticmethod
    async def get_last_block(network: str):
        node = NodeFactory.create_node(network)
        last_block = await node.get_last_block()
        return last_block

    def get_transaction_stream_challenge_query(self, network: str, block_height: int):
        if network == NETWORK_COMMUNE:
            return "SELECT 1 as result;"
        if network == NETWORK_BITCOIN:
            return f"""
            WITH block_inputs AS (
                SELECT COALESCE(SUM(amount), 0) as total_inputs
                FROM transaction_inputs
                WHERE block_height = {block_height}
            ),
            block_outputs AS (
                SELECT COALESCE(SUM(amount), 0) as total_outputs
                FROM transaction_outputs
                WHERE block_height = {block_height}
            ),
            block_transactions AS (
                SELECT COALESCE(SUM(in_total_amount) + SUM(out_total_amount) + SUM(fee_amount), 0) as total_tx_amounts
                FROM transactions
                WHERE block_height = {block_height}
            )
            SELECT COALESCE(
                (SELECT total_inputs FROM block_inputs) +
                (SELECT total_outputs FROM block_outputs) +
                (SELECT total_tx_amounts FROM block_transactions),
                0
            ) as result;
            """
        raise NotImplementedError(f"Unsupported network: {network}")

    def get_balance_tracking_challenge_query(self, network: str, block_height: int):
        if network == NETWORK_COMMUNE:
            return "SELECT 1 as result;"
        if network == NETWORK_BITCOIN:
            return f"""
                WITH address_balances AS (
                    SELECT COALESCE(SUM(balance), 0) as total_balance
                    FROM balance_address_blocks 
                    WHERE block_height = {block_height}
                ),
                balance_deltas AS (
                    SELECT COALESCE(SUM(balance_delta), 0) as total_delta
                    FROM balance_changes 
                    WHERE block_height = {block_height}
                ),
                block_heights AS (
                    SELECT block_height as height
                    FROM blocks 
                    WHERE block_height = {block_height}
                )
                SELECT COALESCE(
                    (SELECT total_balance FROM address_balances) +
                    (SELECT total_delta FROM balance_deltas) +
                    (SELECT height FROM block_heights),
                    0
                ) as result;
                """
        raise NotImplementedError(f"Unsupported network: {network}")

    def get_money_flow_challenge_query(self, network: str, block_height: int) -> str:
        if network == NETWORK_COMMUNE:
            return "RETURN 1"
        if network == NETWORK_BITCOIN:
            return f"""
            WITH {block_height} as height
            MATCH (a1:Address)-[s1:SENT]->(t:Transaction)
            WHERE t.block_height = height
            WITH COALESCE(SUM(s1.amount), 0) as total_addr_to_tx
    
            MATCH (t:Transaction)-[s2:SENT]->(a2:Address)
            WHERE t.block_height = height
            WITH total_addr_to_tx, COALESCE(SUM(s2.amount), 0) as total_tx_to_addr
    
            MATCH (a1:Address)-[s3:SENT]->(a2:Address)
            WHERE s3.block_height = height
            WITH total_addr_to_tx, total_tx_to_addr, COALESCE(SUM(s3.amount), 0) as total_addr_to_addr
    
            RETURN COALESCE(
                total_addr_to_tx + 
                total_tx_to_addr + 
                total_addr_to_addr,
                0
            ) as result
            """
        raise NotImplementedError(f"Unsupported network: {network}")

    async def challenge_miners(self, network: str) -> dict:
        start_time = time.time()
        miners = await self.miner_discovery_manager.get_miners_by_network(network)
        challenge_results = await self._challenge_miners(network, miners)
        miner_keys = {miner['miner_key'] for miner in miners}

        with open('subnet/validator/miner_senate.json', 'r') as file:
            miner_senate = json.load(file)

        # Configuration constants
        MIN_SENATE_RESPONSES = 3
        MIN_CONSENSUS_PERCENTAGE = 66  # Required percentage for both senate and majority consensus
        MAX_RESPONSE_TIME = 10  # seconds

        results = {
            'status': 'success',
            'validation_time': 0,
            'consensus_mode': None,
            'model_kinds': {},
            'metrics': {
                'total_miners': len(miner_keys),
                'total_senate': len(miner_senate['senate'][network]['miners']),
                'responding_miners': 0
            }
        }

        senate_consensus_enabled = miner_senate['senate'][network]['enabled']
        senate_miners = set(miner_senate['senate'][network]['miners']) if senate_consensus_enabled else set()
        results['consensus_mode'] = 'senate' if senate_consensus_enabled else 'majority'

        # Process each model kind
        for model_kind in challenge_results:
            results['model_kinds'][model_kind] = {
                'status': 'pending',
                'consensus': {
                    'hash': None,
                    'agreement_percentage': 0,
                    'total_responses': 0
                },
                'miners': {},
                'timing': {
                    'start_time': time.time(),
                    'completion_time': None,
                    'duration': None
                }
            }

            # Collect all responses for this model kind
            valid_responses = {}
            for miner_key in challenge_results[model_kind]:
                response_time = time.time() - start_time
                if response_time <= MAX_RESPONSE_TIME:
                    valid_responses[miner_key] = challenge_results[model_kind][miner_key]

            total_responses = len(valid_responses)
            results['model_kinds'][model_kind]['consensus']['total_responses'] = total_responses

            if senate_consensus_enabled:
                # Senate consensus mode
                senate_responses = {k: v for k, v in valid_responses.items() if k in senate_miners}

                if len(senate_responses) < MIN_SENATE_RESPONSES:
                    results['model_kinds'][model_kind]['status'] = 'failed'
                    results['model_kinds'][model_kind]['consensus']['error'] = 'insufficient_senate_responses'
                    continue

                response_pool = senate_responses
            else:
                # Majority consensus mode
                if not valid_responses:
                    results['model_kinds'][model_kind]['status'] = 'failed'
                    results['model_kinds'][model_kind]['consensus']['error'] = 'no_responses'
                    continue

                response_pool = valid_responses

            # Count hashes for consensus determination
            hash_counts = {}
            for hash_value in response_pool.values():
                hash_counts[hash_value] = hash_counts.get(hash_value, 0) + 1

            # Find hash with highest agreement
            max_agreements = max(hash_counts.values())
            consensus_candidates = [h for h, count in hash_counts.items() if count == max_agreements]

            # Calculate consensus percentage based on responding miners in the selected pool
            consensus_percentage = (max_agreements / len(response_pool)) * 100

            # Check for clear consensus
            if len(consensus_candidates) > 1 or consensus_percentage < MIN_CONSENSUS_PERCENTAGE:
                results['model_kinds'][model_kind]['status'] = 'no_consensus'
                results['model_kinds'][model_kind]['consensus']['error'] = 'no_clear_consensus'
                results['model_kinds'][model_kind]['consensus'].update({
                    'competing_hashes': len(consensus_candidates),
                    'highest_agreement': consensus_percentage
                })
                continue

            consensus_hash = consensus_candidates[0]

            # Update consensus information
            results['model_kinds'][model_kind]['consensus'].update({
                'hash': consensus_hash,
                'agreement_percentage': consensus_percentage
            })

            # Validate all miners against consensus hash
            for miner_key in miner_keys:
                if miner_key in challenge_results[model_kind]:
                    is_valid = challenge_results[model_kind][miner_key] == consensus_hash
                    results['model_kinds'][model_kind]['miners'][miner_key] = {
                        'valid': is_valid,
                        'responded': True,
                        'is_senate': miner_key in senate_miners,
                        'error': None if is_valid else 'hash_mismatch'
                    }
                else:
                    results['model_kinds'][model_kind]['miners'][miner_key] = {
                        'valid': False,
                        'responded': False,
                        'is_senate': miner_key in senate_miners,
                        'error': 'no_response'
                    }

            # Update timing information
            completion_time = time.time()
            results['model_kinds'][model_kind]['timing'].update({
                'completion_time': completion_time,
                'duration': completion_time - results['model_kinds'][model_kind]['timing']['start_time']
            })

            results['model_kinds'][model_kind]['status'] = 'success'

            logger.info(f"Validation complete for model kind",
                        model_kind=model_kind,
                        consensus_mode=results['consensus_mode'],
                        consensus_hash=consensus_hash,
                        agreement_percentage=consensus_percentage,
                        total_responses=total_responses,
                        valid_responses=sum(
                            1 for m in results['model_kinds'][model_kind]['miners'].values() if m['valid']))

        results['validation_time'] = time.time() - start_time
        results['metrics']['responding_miners'] = len(
            {miner for responses in challenge_results.values() for miner in responses})

        return results

    async def _challenge_miners(self, network: str, miners: list[dict]) -> dict:

        last_block = await self.get_last_block(network)
        block_height = select_block(1, last_block, 39)

        queries = {
            MODEL_KIND_TRANSACTION_STREAM: self.get_transaction_stream_challenge_query(network, block_height),
            MODEL_KIND_BALANCE_TRACKING: self.get_balance_tracking_challenge_query(network, block_height),
            MODEL_KIND_MONEY_FLOW: self.get_money_flow_challenge_query(network, block_height)
        }

        model_kinds = [MODEL_KIND_BALANCE_TRACKING, MODEL_KIND_TRANSACTION_STREAM, MODEL_KIND_MONEY_FLOW]

        query_tasks = {}
        for model_kind in model_kinds:
            for query in queries:
                new_tasks = {
                    asyncio.create_task(self._query_miner(miner, model_kind, query)): (miner, time.time())
                    for miner in miners
                }
                query_tasks.update(new_tasks)

        responses = {model_kind: {} for model_kind in model_kinds}

        try:
            pending = set(query_tasks.keys())
            start_time = time.time()

            while pending:
                if time.time() - start_time > self.query_timeout:
                    break

                done, pending = await asyncio.wait(
                    pending,
                    timeout=max(0.0, self.query_timeout - (time.time() - start_time)),
                    return_when=asyncio.FIRST_COMPLETED
                )

                if not done:  # Timeout reached
                    break

                for completed_task in done:
                    try:
                        response = await completed_task
                        current_miner, start_time = query_tasks[completed_task]
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

                        model_kind = response['model_kind']
                        responses[model_kind][miner_key] = result_hash

                    except Exception as e:
                        logger.error(f"Error querying miner", error=e)
                        continue

        finally:
            for task in query_tasks.keys():
                if not task.done():
                    task.cancel()

        return responses

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
        elif model_kind == MODEL_KIND_MONEY_FLOW:
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
