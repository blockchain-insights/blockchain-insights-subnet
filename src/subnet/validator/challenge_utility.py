import asyncio
import threading
from src.subnet.validator._config import ValidatorSettings, load_environment
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.blockchain.common.challenge_generator_factory import ChallengeGeneratorFactory
from src.subnet.protocol.llm_engine import MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING
from src.subnet.validator.logger import logger


async def generate_challenge_and_store(settings: ValidatorSettings, network: str, model: str, challenge_manager, threshold: int):
    challenge_generator = ChallengeGeneratorFactory.create_challenge_generator(network, model, settings)
    await challenge_generator.generate_and_store(challenge_manager, threshold)


async def main(settings: ValidatorSettings, network: str, model: str, frequency: int, threshold: int, terminate_event: threading.Event):
    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)

    # Choose the correct challenge manager based on model type
    if model == MODEL_TYPE_FUNDS_FLOW:
        from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
        challenge_manager = ChallengeFundsFlowManager(session_manager)
    elif model == MODEL_TYPE_BALANCE_TRACKING:
        from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
        challenge_manager = ChallengeBalanceTrackingManager(session_manager)
    else:
        raise ValueError(f"Unsupported model type: {model}")

    try:
        while not terminate_event.is_set():
            try:
                # Generate and store challenges
                await generate_challenge_and_store(settings, network, model, challenge_manager, threshold)
                terminate_event.wait(frequency * 60)  # Wait for the specified frequency
            except asyncio.TimeoutError:
                logger.error("Timeout occurred while generating or storing the challenge.")
    except Exception as e:
        logger.error(f"An error occurred while generating or storing the challenge: {e}")


if __name__ == "__main__":
    import sys
    import signal

    if len(sys.argv) != 6:
        logger.info("Usage: python challenge_utility.py <environment> <network> <model> <frequency_in_minutes> <threshold>")
        sys.exit(1)

    # Parse command-line arguments
    environment = sys.argv[1]
    network = sys.argv[2]
    model = sys.argv[3]  # 'funds_flow' or 'balance_tracking'
    frequency = int(sys.argv[4])
    threshold = int(sys.argv[5])

    # Configure logging
    logger.remove()
    logger.add(
        f"../logs/challenge_utility_{network}_{model}.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    terminate_event = threading.Event()
    load_environment(environment)
    settings = ValidatorSettings()

    def signal_handler(signal_num, frame):
        logger.info("Received termination signal, stopping...")
        terminate_event.set()

    # Handle termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the main function
    asyncio.run(main(settings, network, model, frequency, threshold, terminate_event))

    logger.info("Challenge Utility stopped.")
