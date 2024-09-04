from src.subnet.validator.nodes.ethereum.node import EthereumNode  # Assuming you have an EthereumNode class

from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.blockchain.base_prompt_generator import BasePromptGenerator
import random

ETH_PROMPT_TEMPLATES = [
    "What is the total amount of the transaction with txid {txid} in block {block}?",
    "List all transactions in block {block} and their respective values.",
    "Calculate the gas fees for all transactions in block {block}.",
    "Retrieve the details of the transaction with txid {txid} in block {block}.",
    "Provide the total number of transactions in block {block} and identify the largest by gas fees.",
    "Determine the gas fees for the transaction with txid {txid} in block {block}.",
    "Identify all addresses involved in the transaction with txid {txid} in block {block}."
]

class EthereumPromptGenerator(BasePromptGenerator):
    def __init__(self, settings: ValidatorSettings):
        super().__init__(settings)
        self.node = EthereumNode()  # Assumed EthereumNode handles Ethereum-related operations

    def get_random_txid_and_block(self):
        last_block_height = self.node.get_current_block_height() - 6
        random_block_height = random.randint(0, last_block_height)
        tx_id, block_data = self.node.get_random_txid_from_block(random_block_height)
        return tx_id, random_block_height, block_data

    def generate_prompt(self, tx_id: str, block: str) -> str:
        selected_template = random.choice(ETH_PROMPT_TEMPLATES)
        return selected_template.format(txid=tx_id, block=block)
