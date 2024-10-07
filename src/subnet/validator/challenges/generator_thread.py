import asyncio
import threading
import traceback

from loguru import logger
from src.subnet.protocol import get_networks, NETWORK_BITCOIN, NETWORK_COMMUNE
from src.subnet.validator.challenges import ChallengeGenerator
from src.subnet.validator.challenges.bitcoin_challenge_generator import BitcoinChallengeGenerator
from src.subnet.validator.challenges.commune_challenge_generator import CommuneChallengeGenerator
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager


class ChallengeGeneratorFactory:
    @classmethod
    def create_challenge_generator(cls, network: str, settings, terminate_event: threading.Event) -> ChallengeGenerator:
        challenge_generator_class = {
            NETWORK_BITCOIN: BitcoinChallengeGenerator,
            NETWORK_COMMUNE: CommuneChallengeGenerator
        }.get(network)

        if challenge_generator_class is None:
            raise ValueError(f"Unsupported combination of network: {network}")

        return challenge_generator_class(settings, terminate_event)


class ChallengeGeneratorThread(threading.Thread):
    def __init__(self, settings, environment, frequency, threshold, terminate_event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = settings
        self.environment = environment
        self.frequency = frequency
        self.threshold = threshold
        self.terminate_event = terminate_event

    async def main(self):

        networks = get_networks()
        session_manager = DatabaseSessionManager()
        session_manager.init(self.settings.DATABASE_URL)
        funds_flow_challenge_manager = ChallengeFundsFlowManager(session_manager)
        balance_tracking_challenge_manager = ChallengeBalanceTrackingManager(session_manager)

        try:
            while not self.terminate_event.is_set():
                next_send_time = asyncio.get_event_loop().time() + (self.frequency * 60)

                for network in networks:
                    try:
                        factory = ChallengeGeneratorFactory()
                        generator = factory.create_challenge_generator(network, self.settings, self.terminate_event)
                        if self.terminate_event.is_set():
                            break
                        await generator.funds_flow_generate_and_store(funds_flow_challenge_manager, self.threshold)
                        if self.terminate_event.is_set():
                            break
                        await generator.balance_tracking_generate_and_store(balance_tracking_challenge_manager, self.threshold)
                        if self.terminate_event.is_set():
                            break
                    except asyncio.TimeoutError:
                        logger.error("Timeout occurred while generating or storing the challenge.")

                while not self.terminate_event.is_set():
                    now = asyncio.get_event_loop().time()
                    if now >= next_send_time:
                        break
                    await asyncio.sleep(1)

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"An error occurred while generating or storing the challenge", error=e, traceback=tb)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main())
        finally:
            loop.close()