import json
from threading import Event

from src.subnet.protocol import NETWORK_COMMUNE
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.challenges import ChallengeGenerator
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
from random import randint
from loguru import logger

from src.subnet.validator.nodes.commune import CommuneNode


class CommuneChallengeGenerator(ChallengeGenerator):
    def __init__(self, settings: ValidatorSettings, terminate_event: Event):
        super().__init__(settings, terminate_event)
        self.network = NETWORK_COMMUNE
        self.node = CommuneNode(settings)

    async def funds_flow_generate_and_store(self, challenge_manager: ChallengeFundsFlowManager, threshold: int):
        try:
            last_block_height = self.node.get_current_block_height()
        except NotImplementedError as e:
            logger.error(f"Failed to fetch block height, skipping")
            return

        funds_flow_challenge, tx_id = self.node.create_funds_flow_challenge(last_block_height, self.terminate_event)
        if funds_flow_challenge is None:
            return

        challenge_json = json.dumps(funds_flow_challenge.model_dump())
        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        logger.debug(f"Generated Funds Flow Challenge", network=self.network, challenge=funds_flow_challenge.model_dump())

        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        await challenge_manager.store_challenge(challenge_json, tx_id, self.network)
        logger.info(f"Funds Flow Challenge stored in the database successfully.", network=self.network)

    async def balance_tracking_generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        try:
            last_block_height = self.node.get_current_block_height()
        except NotImplementedError as e:
            logger.error(f"Failed to fetch block height, skipping")
            return

        random_balance_tracking_block = randint(1, last_block_height)

        balance_tracking_challenge, balance_tracking_expected_response = self.node.create_balance_tracking_challenge(random_balance_tracking_block, self.terminate_event)
        if balance_tracking_challenge is None:
            return

        challenge_json = json.dumps(balance_tracking_challenge.model_dump())
        logger.debug(f"Generated Balance Tracking Challenge", network=self.network, challenge=balance_tracking_challenge.model_dump())

        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        await challenge_manager.store_challenge(challenge_json, last_block_height,  balance_tracking_expected_response, self.network)
        logger.info(f"Challenge stored in the database successfully.", network=self.network)



