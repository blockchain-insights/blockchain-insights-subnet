import asyncio
import threading
from src.subnet.validator.llm.factory import LLMFactory
from src.subnet.validator._config import ValidatorSettings, load_environment
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.blockchain.common.prompt_generator_factory import PromptGeneratorFactory
from src.subnet.validator.logger import logger


async def generate_prompt_and_store(settings: ValidatorSettings, network: str, validation_prompt_manager, llm, threshold: int):
    prompt_generator = PromptGeneratorFactory.create_prompt_generator(network, settings, llm)
    await prompt_generator.generate_and_store(validation_prompt_manager, threshold)


async def main(settings: ValidatorSettings, network: str, frequency: int, threshold: int, terminate_event: threading.Event):
    llm = LLMFactory.create_llm(settings)  # LLM setup

    # Initialize the session manager and the validation prompt manager
    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)
    validation_prompt_manager = ValidationPromptManager(session_manager)

    try:
        while not terminate_event.is_set():
            try:
                # Generate and store prompts
                await generate_prompt_and_store(settings, network, validation_prompt_manager, llm, threshold)
                terminate_event.wait(frequency * 60)  # Wait for the specified frequency
            except asyncio.TimeoutError:
                logger.error("Timeout occurred while generating or storing the prompt.")
    except Exception as e:
        logger.error(f"An error occurred while generating or storing the prompt: {e}")


if __name__ == "__main__":
    import sys
    import signal

    if len(sys.argv) != 5:
        logger.info("Usage: python llm_prompt_utility.py <environment> <network> <frequency_in_minutes> <threshold>")
        sys.exit(1)

    # Parse command-line arguments
    environment = sys.argv[1]
    network = sys.argv[2]
    frequency = int(sys.argv[3])
    threshold = int(sys.argv[4])

    # Configure logging
    logger.remove()
    logger.add(
        f"../logs/llm_prompt_utility_{network}.log",
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
    asyncio.run(main(settings, network, frequency, threshold, terminate_event))

    logger.info("LLM Prompt Utility stopped.")
