import random
import asyncio
from datetime import datetime, timedelta
from src.subnet.validator.llm.factory import LLMFactory
from src.subnet.validator._config import ValidatorSettings, load_environment
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager

# Define the list of prompt templates
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

    # Get the current highest block height
    highest_block_height = btc.get_current_block_height()

    # Set the lowest block height (typically block 0 is the genesis block)
    lowest_block_height = 0

    # Calculate a random block height between the lowest and highest
    random_block_height = random.randint(lowest_block_height, highest_block_height)

    # Get a random vin or vout address from the random block and also get block data
    random_txid = btc.get_random_txid_from_block(random_block_height)
    print(f"Random Txid: {random_txid}")
    print(f"Block Data: {random_txid['block_data']}")  # Print block data if needed

    # Randomly select a prompt template
    selected_template = random.choice(PROMPT_TEMPLATES)

    # Use the selected template, txid, and block in the LLM prompt generation
    prompt = llm.build_prompt_from_txid_and_block(random_txid['txid'], random_block_height, network, prompt_template=selected_template)
    print(f"Generated Prompt: {prompt}")

    # Check the current number of prompts in the database
    current_prompt_count = await validation_prompt_manager.get_prompt_count()

    if current_prompt_count >= threshold:
        # If the threshold is reached, delete the oldest prompt before storing the new one
        await validation_prompt_manager.delete_oldest_prompt()

    # Store the generated prompt and block information in the database
    await validation_prompt_manager.store_prompt(prompt, random_txid['block_data'])
    print(f"Prompt stored in the database successfully.")


async def main(network: str, frequency: int, threshold: int):
    # Ensure environment is loaded
    env = 'testnet'  # or 'mainnet' depending on your test
    load_environment(env)

    settings = ValidatorSettings()
    llm = LLMFactory.create_llm(settings)

    # Initialize session manager and ValidationPromptManager
    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)
    validation_prompt_manager = ValidationPromptManager(session_manager)

    try:
        while True:
            await generate_prompt_and_store(network, validation_prompt_manager, llm, threshold)
            await asyncio.sleep(frequency * 60)  # frequency is in minutes

    except Exception as e:
        print(f"An error occurred while generating or storing the prompt: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python llm_prompt_utility.py <network> <frequency_in_minutes> <threshold>")
        sys.exit(1)

    network = sys.argv[1]
    frequency = int(sys.argv[2])
    threshold = int(sys.argv[3])

    # Run the async main function
    asyncio.run(main(network, frequency, threshold))
