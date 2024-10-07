import json

from loguru import logger
from src.subnet.protocol import NETWORK_BITCOIN
from src.subnet.validator.challenges import ChallengeGenerator
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.nodes.random_block import select_block


class BitcoinChallengeGenerator(ChallengeGenerator):
    def __init__(self, settings, terminate_event):
        super().__init__(settings, terminate_event)
        self.node = BitcoinNode()
        self.network = NETWORK_BITCOIN

    async def funds_flow_generate_and_store(self, challenge_manager: ChallengeFundsFlowManager, threshold: int):
        last_block_height = self.node.get_current_block_height() - 6

        funds_flow_challenge, tx_id = self.node.create_funds_flow_challenge(last_block_height, self.terminate_event)
        if funds_flow_challenge is None:
            return

        challenge_json = json.dumps(funds_flow_challenge.model_dump())
        logger.debug(f"Generated Funds Flow Challenge", network=self.network, challenge=funds_flow_challenge.model_dump())

        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        await challenge_manager.store_challenge(challenge_json, tx_id, self.network)
        logger.info(f"Challenge stored in the database successfully.", network=self.network)

    async def balance_tracking_generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        last_block = self.node.get_current_block_height() - 6
        random_balance_tracking_block = select_block(0, last_block)

        balance_tracking_challenge, balance_tracking_expected_response = self.node.create_balance_tracking_challenge(random_balance_tracking_block, self.terminate_event)
        if balance_tracking_challenge is None:
            return

        challenge_json = balance_tracking_challenge.json()
        logger.debug(f"Generated Balance Tracking Challenge", network=self.network, challenge=balance_tracking_challenge.model_dump())

        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        await challenge_manager.store_challenge(challenge_json, random_balance_tracking_block, balance_tracking_expected_response, self.network)
        logger.info(f"Challenge stored in the database successfully.", network=self.network)
