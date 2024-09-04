import random
import asyncio
import threading
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
    last_block_height = btc.get_current_block_height() - 6
    lowest_block_height = 0
    random_block_height = select_block(lowest_block_height, last_block_height)
    random_txid = btc.get_random_txid_from_block(random_block_height)
    logger.debug(f"Random Txid: {random_txid}")

    selected_template = random.choice(PROMPT_TEMPLATES)
    prompt = llm.build_prompt_from_txid_and_block(random_txid['txid'], random_block_height, network, prompt_template=selected_template)
    logger.debug(f"Generated Challenge Prompt: {prompt}")
    current_prompt_count = await validation_prompt_manager.get_prompt_count()
    if current_prompt_count >= threshold:
        await validation_prompt_manager.try_delete_oldest_prompt()

    await validation_prompt_manager.store_prompt(prompt, random_txid['block_data'])
    logger.info(f"Prompt stored in the database successfully.")


async def main(network: str, frequency: int, threshold: int, terminate_event: threading.Event):
    settings = ValidatorSettings()
    llm = LLMFactory.create_llm(settings)

    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)
    validation_prompt_manager = ValidationPromptManager(session_manager)

    try:
        while not terminate_event.is_set():
            try:
                await generate_prompt_and_store(network, validation_prompt_manager, llm, threshold)
                terminate_event.wait(frequency * 60)
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

    terminate_event = threading.Event()
    load_environment(environment)

    def signal_handler(signal_num, frame):
        logger.info("Received termination signal, stopping...")
        terminate_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(main(network, frequency, threshold, terminate_event))

    logger.info("LLM Prompt Utility stopped.")
