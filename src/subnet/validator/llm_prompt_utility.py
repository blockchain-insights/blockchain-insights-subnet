import random
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from src.subnet.validator.llm.factory import LLMFactory
from src.subnet.validator._config import ValidatorSettings, load_environment
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.nodes.random_block import select_block

PROMPT_TEMPLATES = [
    "Give me the total amount of the transaction with txid {txid} in block {block}.",
    "List all transactions in block {block} and their respective amounts.",
    "Calculate the sum of incoming and outgoing coins for all transactions in block {block}.",
    "Retrieve the details of the transaction with txid {txid} in block {block}.",
    "Provide the total number of transactions in block {block} and identify the largest transaction by amount.",
    "Determine the fees paid for the transaction with txid {txid} in block {block}.",
    "Identify all addresses involved in the transaction with txid {txid} in block {block}."
]


async def generate_prompt_and_store(network: str, validation_prompt_manager, llm, threshold: int):
    btc = BitcoinNode()

    # Get the current highest block height with some tolerance (6)
    last_block_height = btc.get_current_block_height() - 6

    # Set the lowest block height (typically block 0 is the genesis block)
    lowest_block_height = 0

    # Calculate a random block height between the lowest and highest
    random_block_height = select_block(lowest_block_height, last_block_height)

    # Get a random txid from the random block and also get block data
    random_txid = btc.get_random_txid_from_block(random_block_height)
    logger.debug(f"Random Txid: {random_txid}")
    logger.debug(f"Block Data: {random_txid['block_data']}")  # Print block data if needed

    # Randomly select a prompt template
    selected_template = random.choice(PROMPT_TEMPLATES)

    # Use the selected template, txid, and block in the LLM prompt generation
    prompt = llm.build_prompt_from_txid_and_block(random_txid['txid'], random_block_height, network, prompt_template=selected_template)
    logger.info(f"Generated Prompt: {prompt}")

    # Check the current number of prompts in the database
    current_prompt_count = await validation_prompt_manager.get_prompt_count()

    if current_prompt_count >= threshold:
        # If the threshold is reached, delete the oldest prompt before storing the new one
        await validation_prompt_manager.try_delete_oldest_prompt()

    # Store the generated prompt and block information in the database
    await validation_prompt_manager.store_prompt(prompt, random_txid['block_data'])
    logger.info(f"Prompt stored in the database successfully.")


async def main(network: str, frequency: int, threshold: int, stop_event: asyncio.Event):
    # Ensure environment is loaded
    settings = ValidatorSettings()
    llm = LLMFactory.create_llm(settings)

    # Initialize session manager and ValidationPromptManager
    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)
    validation_prompt_manager = ValidationPromptManager(session_manager)

    try:
        while not stop_event.is_set():
            await generate_prompt_and_store(network, validation_prompt_manager, llm, threshold)
            try:
                # Wait for the stop_event to be set, with a timeout for the frequency interval
                await asyncio.wait_for(stop_event.wait(), timeout=frequency * 60)
            except asyncio.TimeoutError:
                # Continue the loop if the timeout occurs and stop_event is not set
                pass
    except Exception as e:
        logger.error(f"An error occurred while generating or storing the prompt: {e}")


if __name__ == "__main__":
    import sys
    import signal

    if len(sys.argv) != 5:
        logger.info("Usage: python llm_prompt_utility.py <environment> <network> <frequency_in_minutes> <threshold>")
        sys.exit(1)

    environment = sys.argv[1]
    network = sys.argv[2]
    frequency = int(sys.argv[3])
    threshold = int(sys.argv[4])

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

    stop_event = asyncio.Event()

    load_environment(environment)

    def signal_handler(signal_num, frame):
        logger.info("Received termination signal, stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(main(network, frequency, threshold, stop_event))
