from substrateinterface import SubstrateInterface

from src.subnet.protocol import NETWORK_COMMUNE
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.challenges import ChallengeGenerator
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
from random import randint
from loguru import logger

from src.subnet.validator.nodes.commune import CommuneNode


class CommuneChallengeGenerator(ChallengeGenerator):
    def __init__(self, settings: ValidatorSettings):
        super().__init__(settings)
        self.network = NETWORK_COMMUNE
        self.node = CommuneNode(settings)

    async def funds_flow_generate_and_store(self, challenge_manager: ChallengeFundsFlowManager, threshold: int):
        last_block_height = self.node.get_current_block_height() - 6
        funds_flow_challenge, tx_id = self.node.create_funds_flow_challenge(last_block_height)

        challenge_json = funds_flow_challenge.dumps()
        logger.debug(f"Generated Ethereum Funds Flow Challenge: {challenge_json}")

        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        await challenge_manager.store_challenge(challenge_json, tx_id, self.network)
        logger.info(f"Ethereum Funds Flow Challenge stored in the database successfully.")

    async def balance_tracking_generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        random_balance_tracking_block = randint(1, 1000)

        balance_tracking_challenge, balance_tracking_expected_response = self.node.create_balance_tracking_challenge(random_balance_tracking_block)
        challenge_json = balance_tracking_challenge.dumps()
        logger.debug(f"Generated Balance Tracking Challenge: {challenge_json}")

        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        await challenge_manager.store_challenge(challenge_json, balance_tracking_expected_response, self.network)
        logger.info(f"Challenge stored in the database successfully.")



