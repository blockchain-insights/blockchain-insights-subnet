from src.subnet.validator.blockchain.common.balance_tracking.base_challenge_generator import BaseChallengeGenerator
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from random import randint

from src.subnet.validator.logger import logger


class ChallengeGenerator(BaseChallengeGenerator):
    def __init__(self, settings):
        super().__init__(settings)
        #self.node = EthereumNode()  # Use Ethereum-specific node
        self.network = "ethereum"  # Set network to Ethereum

    async def generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        # Retrieve block details (this is for fast testing only, change in production)
        random_balance_tracking_block = randint(1, 1000)

        # Generate a balance tracking challenge
        balance_tracking_challenge, balance_tracking_expected_response = self.node.create_balance_tracking_challenge(random_balance_tracking_block)

        # Convert the challenge object to JSON string
        challenge_json = balance_tracking_challenge.dumps()
        logger.debug(f"Generated Balance Tracking Challenge: {challenge_json}")

        # Check if the current challenge count has exceeded the threshold
        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        # Store the challenge JSON and block height in the database
        await challenge_manager.store_challenge(challenge_json, balance_tracking_expected_response, self.network)
        logger.info(f"Challenge stored in the database successfully.")
