import random
from loguru import logger
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode  # This can be substituted for EthereumNode if needed
from src.subnet.validator.blockchain.common.balance_tracking.base_challenge_generator import BaseChallengeGenerator
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from random import randint


class ChallengeGenerator(BaseChallengeGenerator):
    def __init__(self, settings):
        super().__init__(settings)
        self.node = BitcoinNode()  # You can substitute this with EthereumNode for Ethereum challenges
        self.network = "bitcoin"  # You can change this to "ethereum" for Ethereum challenges

    async def generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        # Retrieve block details
        random_balance_tracking_block = randint(1, 1000)  # this is for fast testing only, remove on production

        # Generate a balance tracking challenge
        balance_tracking_challenge, balance_tracking_expected_response = self.node.create_balance_tracking_challenge(random_balance_tracking_block)
        # Convert the challenge object to JSON string
        challenge_json = balance_tracking_challenge.dumps()
        logger.debug(f"Generated Funds Flow Challenge: {challenge_json}")

        # Check if the current challenge count has exceeded the threshold
        current_challenge_count = await challenge_manager.get_challenge_count(self.network)
        if current_challenge_count >= threshold:
            await challenge_manager.try_delete_oldest_challenge(self.network)

        # Store the challenge JSON and transaction ID in the database
        await challenge_manager.store_challenge(challenge_json, balance_tracking_expected_response, self.network)
        logger.info(f"Challenge stored in the database successfully.")
