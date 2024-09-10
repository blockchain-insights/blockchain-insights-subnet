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
        "Identify all addresses involved in the transaction with txid {txid} in block {block}."
    ]

    def __init__(self, settings, llm: BaseLLM):
        super().__init__(settings)
        self.node = BitcoinNode()  # Bitcoin-specific node
        self.llm = llm  # LLM instance passed to use for prompt generation
        self.network = "bitcoin"  # Store network as a class member

    def create_graph_funds_flow_graph(self, block_data, batch_size=8):
        transactions = block_data.transactions

        # Initialize an empty dictionary to hold the graph data
        graph_data = {
            "outputs": []
        }

        try:
            for i in range(0, len(transactions), batch_size):
                batch_transactions = transactions[i: i + batch_size]

                for tx in batch_transactions:
                    # Process the transaction and get all input and output data
                    in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = self.node.process_in_memory_txn_for_indexing(
                        tx)

                    # Create nodes for all input addresses
                    for address in input_addresses:
                        graph_data["outputs"].append({
                            "type": "node",
                            "id": address,
                            "label": f"Address: {address}",
                            "balance": in_amount_by_address[address],  # Balance for this transaction's input
                            "timestamp": tx.timestamp,
                            "block_height": tx.block_height
                        })

                    # Create nodes for all output addresses
                    for address in output_addresses:
                        graph_data["outputs"].append({
                            "type": "node",
                            "id": address,
                            "label": f"Address: {address}",
                            "balance": out_amount_by_address[address],  # Balance for this transaction's output
                            "timestamp": tx.timestamp,
                            "block_height": tx.block_height
                        })

                    # Create edges between input and output addresses
                    for in_address in input_addresses:
                        for out_address in output_addresses:
                            graph_data["outputs"].append({
                                "type": "edge",
                                "id": f"{tx.tx_id}-{in_address}->{out_address}",
                                "label": f"Transaction: {tx.tx_id}",
                                "from_id": in_address,
                                "to_id": out_address
                            })

            # Return the graph data conforming to the schema
            return graph_data

        except Exception as e:
            logger.error(f"An exception occurred: {str(e)}")
            return None

    async def generate_and_store(self, validation_prompt_manager: ValidationPromptManager, threshold: int):
        # Retrieve block details
        last_block_height = self.node.get_current_block_height() - 6
        random_block_height = random.randint(0, last_block_height)
        tx_id, block_data = self.node.get_random_txid_from_block(random_block_height)
        parsed_block_data = parse_block_data(block_data)
        normalized_block_data = self.create_graph_funds_flow_graph(parsed_block_data)

        logger.debug(f"Random Txid: {tx_id}")

        selected_template = random.choice(self.PROMPT_TEMPLATES)
        prompt = self.llm.build_prompt_from_txid_and_block(tx_id, random_block_height, self.network, prompt_template=selected_template)
        logger.debug(f"Generated Challenge Prompt: {prompt}")

        current_prompt_count = await validation_prompt_manager.get_prompt_count(self.network)
        if current_prompt_count >= threshold:
            await validation_prompt_manager.try_delete_oldest_prompt(self.network)

        await validation_prompt_manager.store_prompt(prompt, normalized_block_data, self.network)
        logger.info(f"Prompt stored in the database successfully.")
