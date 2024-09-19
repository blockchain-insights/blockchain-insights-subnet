import json
import random
from loguru import logger
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode
from src.subnet.validator.blockchain.common.base_prompt_generator import BasePromptGenerator
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.llm.base_llm import BaseLLM
from src.subnet.validator.nodes.bitcoin.node_utils import parse_block_data


class PromptGenerator(BasePromptGenerator):
    PROMPT_TEMPLATES = [
        "Give me the total amount of the transaction with txid {txid} in block {block}.",
        "List all transactions in block {block} and their respective amounts.",
        "Calculate the sum of incoming and outgoing coins for all transactions in block {block}.",
        "Retrieve the details of the transaction with txid {txid} in block {block}.",
        "Provide the total number of transactions in block {block} and identify the largest transaction by amount.",
        "Determine the fees paid for the transaction with txid {txid} in block {block}.",
        "Identify all addresses involved in the transaction with txid {txid} in block {block}.",
        "List the top 3 balances in block {block}, along with their respective amounts and timestamps.",
        "Identify the largest balance change in block {block} and provide the associated timestamp.",
        "Determine the total sum of balances for all addresses in block {block} and return the block's timestamp.",
        "Retrieve the top 3 balance increases in block {block} and return the corresponding amounts and timestamps.",
        "Provide the total number of balance changes in block {block} and identify the highest balance after the block is processed.",
        "Return all balance adjustments made in block {block}, including the block's timestamp and the highest balance.",
        "Calculate the total BTC held in block {block} and identify the block's timestamp."
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
        logger.debug(f"Random tx_id", tx_id=tx_id)

        selected_template = random.choice(self.PROMPT_TEMPLATES)
        prompt = self.llm.build_prompt_from_txid_and_block(tx_id, random_block_height, self.network, prompt_template=selected_template)
        logger.debug(f"Generated Challenge Prompt", prompt=prompt)
        prompt_model_type = self.llm.determine_model_type(prompt, self.network)

        parsed_block_data = json.dumps(parse_block_data(block_data))
        current_prompt_count = await validation_prompt_manager.get_prompt_count(self.network)
        if current_prompt_count >= threshold:
            await validation_prompt_manager.try_delete_oldest_prompt(self.network)

        await validation_prompt_manager.store_prompt(prompt, prompt_model_type, parsed_block_data, self.network)
        logger.info(f"Prompt stored in the database successfully.")
