import random
from src.subnet.protocol.llm_engine import MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING
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
            "outputs": [
                {
                    "type": "graph",
                    "result": []
                }
            ]
        }

        try:
            for i in range(0, len(transactions), batch_size):
                batch_transactions = transactions[i: i + batch_size]

                for tx in batch_transactions:
                    in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = self.node.process_in_memory_txn_for_indexing(tx)

                    # Create nodes for all input addresses
                    for address in input_addresses:
                        graph_data["outputs"][0]["result"].append({
                            "type": "node",
                            "id": address,
                            "label": "address"
                        })

                    # Create nodes for all output addresses
                    for address in output_addresses:
                        graph_data["outputs"][0]["result"].append({
                            "type": "node",
                            "id": address,
                            "label": "address"
                        })

                    # Create a node for the transaction
                    graph_data["outputs"][0]["result"].append({
                        "type": "node",
                        "id": tx.tx_id,
                        "label": "transaction",
                        "balance": out_total_amount,  # Balance output by the transaction
                        "timestamp": tx.timestamp,
                        "block_height": tx.block_height
                    })

                    # Create edges from input addresses to the transaction node
                    for in_address in input_addresses:
                        edge_id = f"{in_address}-{tx.tx_id}"
                        graph_data["outputs"][0]["result"].append({
                            "type": "edge",
                            "id": edge_id,
                            "label": f"{in_amount_by_address[in_address]:.8f} BTC",
                            "from_id": in_address,
                            "to_id": tx.tx_id
                        })

                    # Create edges from the transaction node to output addresses
                    for out_address in output_addresses:
                        edge_id = f"{tx.tx_id}-{out_address}"
                        graph_data["outputs"][0]["result"].append({
                            "type": "edge",
                            "id": edge_id,
                            "label": f"{out_amount_by_address[out_address]:.8f} BTC",
                            "from_id": tx.tx_id,
                            "to_id": out_address
                        })
            return graph_data

        except Exception as e:
            logger.error(f"An exception occurred: {str(e)}")
            return None

    async def generate_and_store(self, validation_prompt_manager: ValidationPromptManager, threshold: int):
        # Retrieve block details
        last_block_height = self.node.get_current_block_height() - 6
        random_block_height = random.randint(0, last_block_height)
        tx_id, block_data = self.node.get_random_txid_from_block(random_block_height)
        logger.debug(f"Random Txid: {tx_id}")

        selected_template = random.choice(self.PROMPT_TEMPLATES)
        prompt = self.llm.build_prompt_from_txid_and_block(tx_id, random_block_height, self.network, prompt_template=selected_template)
        logger.debug(f"Generated Challenge Prompt: {prompt}")
        prompt_model_type = self.llm.determine_model_type(prompt, self.network)

        parsed_block_data = parse_block_data(block_data)
        transformed_block_data = None
        if prompt_model_type == MODEL_TYPE_FUNDS_FLOW:
            transformed_block_data = self.create_graph_funds_flow_graph(parsed_block_data)
        if prompt_model_type == MODEL_TYPE_BALANCE_TRACKING:
            transformed_block_data = None
            # TODO: Implement balance tracking graph generation

        current_prompt_count = await validation_prompt_manager.get_prompt_count(self.network)
        if current_prompt_count >= threshold:
            await validation_prompt_manager.try_delete_oldest_prompt(self.network)

        await validation_prompt_manager.store_prompt(prompt, prompt_model_type, transformed_block_data, self.network)
        logger.info(f"Prompt stored in the database successfully.")
