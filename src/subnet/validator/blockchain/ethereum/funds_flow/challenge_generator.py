from src.subnet.validator.blockchain.common.funds_flow.base_challenge_generator import BaseChallengeGenerator
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
from loguru import logger


class ChallengeGenerator(BaseChallengeGenerator):
    def __init__(self, settings):
        super().__init__(settings)
        #self.node = EthereumNode()  # Use Ethereum-specific node
        self.network = "ethereum"  # Set network to Ethereum

    async def generate_and_store(self, challenge_manager: ChallengeFundsFlowManager, threshold: int):
        # Retrieve block details
        last_block_height = self.node.get_current_block_height() - 6

        # Generate a funds flow challenge
        funds_flow_challenge, tx_id = self.node.create_funds_flow_challenge(0, last_block_height)

        # Convert the challenge object to JSON string
        challenge_json = funds_flow_challenge.dumps()
        logger.debug(f"Generated Ethereum Funds Flow Challenge: {challenge_json}")

        # Check if the current challenge count has exceeded the threshold
        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        # Store the challenge JSON and transaction ID in the database
        await challenge_manager.store_challenge(challenge_json, tx_id, self.network)
        logger.info(f"Ethereum Funds Flow Challenge stored in the database successfully.")
