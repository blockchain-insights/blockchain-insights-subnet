import random
from loguru import logger
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode
from src.subnet.validator.blockchain.base_prompt_generator import BasePromptGenerator
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.llm.base_llm import BaseLLM

class BitcoinPromptGenerator(BasePromptGenerator):
    PROMPT_TEMPLATES = [
        "Give me the total amount of the transaction with txid {txid} in block {block}.",
        "List all transactions in block {block} and their respective amounts.",
        "Calculate the sum of incoming and outgoing coins for all transactions in block {block}.",
        "Retrieve the details of the transaction with txid {txid} in block {block}.",
        "Provide the total number of transactions in block {block} and identify the largest transaction by amount.",
        "Determine the fees paid for the transaction with txid {txid} in block {block}.",
        "Identify all addresses involved in the transaction with txid {txid} in block {block}."
    ]

    def __init__(self, settings, llm: BaseLLM):
        super().__init__(settings)
        self.node = BitcoinNode()  # Bitcoin-specific node
        self.llm = llm  # LLM instance passed to use for prompt generation
        self.network = "bitcoin"  # Store network as a class member

    async def generate_and_store(self, validation_prompt_manager: ValidationPromptManager, threshold: int):
        # Retrieve block details
        last_block_height = self.node.get_current_block_height() - 6
        random_block_height = random.randint(0, last_block_height)
        tx_id, block_data = self.node.get_random_txid_from_block(random_block_height)
        logger.debug(f"Random Txid: {tx_id}")

        # Randomly select a prompt template
        selected_template = random.choice(self.PROMPT_TEMPLATES)
        prompt = self.llm.build_prompt_from_txid_and_block(tx_id, random_block_height, self.network, prompt_template=selected_template)
        logger.debug(f"Generated Challenge Prompt: {prompt}")

        # Check if the current prompt count has exceeded the threshold
        current_prompt_count = await validation_prompt_manager.get_prompt_count(self.network)
        if current_prompt_count >= threshold:
            await validation_prompt_manager.try_delete_oldest_prompt(self.network)

        # Store the prompt and block data in the database
        await validation_prompt_manager.store_prompt(prompt, block_data, self.network)
        logger.info(f"Prompt stored in the database successfully.")
