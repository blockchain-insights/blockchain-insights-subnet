from typing import List, Dict, Any, Set
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc
from loguru import logger


class BitcoinGraphTransformer(BaseGraphTransformer):
    def __init__(self):
        self.output_data: List[Dict[str, Any]] = []
        self.transaction_ids: Set[str] = set()
        self.address_ids: Set[str] = set()
        self.edge_ids: Set[str] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug("Transforming result")
        self.output_data = []
        self.transaction_ids = set()
        self.address_ids = set()
        self.edge_ids = set()

        for entry in result:
            try:
                self.process_transaction_entry(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}, Entry: {entry}")
        return self.output_data

    def process_transaction_entry(self, entry: Dict[str, Any]) -> None:
        logger.debug(f"Processing Entry: {entry}")

        # Process the main transaction, sender, and recipient
        address_node = self.validate_dict_entry(entry.get('a1'), 'a1')
        recipient_node = self.validate_dict_entry(entry.get('a2'), 'a2')
        transaction_node = self.validate_dict_entry(entry.get('t1'), 't1')

        if not transaction_node:
            logger.warning("Skipping entry due to missing transaction node (t1).")
            return

        tx_id = transaction_node.get('tx_id')

        # Process transaction node
        if tx_id and tx_id not in self.transaction_ids:
            self.output_data.append({
                "id": tx_id,
                "type": "node",
                "label": "transaction",
                "balance": satoshi_to_btc(transaction_node.get('out_total_amount', 0)),
                "timestamp": transaction_node.get('timestamp'),
                "block_height": transaction_node.get('block_height')
            })
            self.transaction_ids.add(tx_id)

        # Process address nodes (a1 and a2)
        self.add_address_node(address_node, 'address')
        self.add_address_node(recipient_node, 'recipient')

        address = address_node.get('address')
        recipient = recipient_node.get('address')

        # Process edges from sender to transaction and transaction to recipient
        sent_transactions1 = self.validate_dict_entry(entry.get('s1'), 's1')
        sent_transactions2 = self.validate_dict_entry(entry.get('s2'), 's2')

        self.process_sent_edges(sent_transactions1, address, tx_id)
        self.process_sent_edges(sent_transactions2, tx_id, recipient)

        # NEW: Process path if it exists in the entry
        path = entry.get('path')
        if path:
            self.process_path(path)

    def process_path(self, path: List[Any]) -> None:
        """Process the path field to extract nodes and edges."""
        logger.debug(f"Processing path: {path}")

        prev_node = None
        prev_tx = None
        for element in path:
            if isinstance(element, dict):
                if 'address' in element:
                    # It's an address node
                    address = element.get('address')
                    if address and address not in self.address_ids:
                        self.output_data.append({
                            "id": address,
                            "type": "node",
                            "label": "address",
                            "name": element.get('name')  # Capture name if available
                        })
                        self.address_ids.add(address)

                    if prev_tx and prev_node:
                        # Create an edge between previous node and current transaction
                        self.process_sent_edges([prev_tx], prev_node, address)

                    prev_node = address  # Update the previous node as current address

                elif 'tx_id' in element:
                    # It's a transaction node
                    tx_id = element.get('tx_id')
                    if tx_id and tx_id not in self.transaction_ids:
                        self.output_data.append({
                            "id": tx_id,
                            "type": "node",
                            "label": "transaction",
                            "balance": satoshi_to_btc(element.get('out_total_amount', 0)),
                            "timestamp": element.get('timestamp'),
                            "block_height": element.get('block_height')
                        })
                        self.transaction_ids.add(tx_id)

                    prev_tx = element  # Update the previous transaction
            elif isinstance(element, str):
                # This could be an edge label like "SENT", skip for now
                continue

    def add_address_node(self, address_node: Dict[str, Any], label: str) -> None:
        """Helper to add address nodes to the output, ensuring no duplicates."""
        address = address_node.get('address')
        if address and address not in self.address_ids:
            self.output_data.append({
                "id": address,
                "type": "node",
                "label": "address",
                "name": address_node.get('name')  # Ensure to capture 'name' if available
            })
            self.address_ids.add(address)

    def process_sent_edges(self, sent_transactions: List[Any], from_id: str, to_id: str) -> None:
        """Process a list of SENT edges and add them to the output."""
        if not sent_transactions or not isinstance(sent_transactions, list):
            logger.warning(f"Skipping edge creation due to invalid sent transactions.")
            return

        # Iterate over the sent transactions in the list and extract relevant data
        for sent_transaction in sent_transactions:
            if isinstance(sent_transaction, dict):
                block_height = sent_transaction.get('block_height')
                tx_id = sent_transaction.get('tx_id')
                value_satoshi = sent_transaction.get('value_satoshi')

                edge_id = f"{from_id}-{to_id}"
                if from_id and to_id and edge_id not in self.edge_ids:
                    edge_label = f"{satoshi_to_btc(value_satoshi):.8f} BTC" if value_satoshi else "SENT"

                    self.output_data.append({
                        "id": edge_id,
                        "type": "edge",
                        "label": edge_label,
                        "from_id": from_id,
                        "to_id": to_id,
                        "block_height": block_height,
                        "tx_id": tx_id,
                        "satoshi_value": value_satoshi,  # Include satoshi value in the output
                        "btc_value": satoshi_to_btc(value_satoshi)  # Include BTC value conversion in the output
                    })
                    self.edge_ids.add(edge_id)

                    logger.debug(
                        f"Processed Edge: {edge_id}, Label: {edge_label}, Block: {block_height}, Tx: {tx_id}, BTC Value: {satoshi_to_btc(value_satoshi):.8f}")

            elif isinstance(sent_transaction, list):
                # Handle case where a transaction is nested within a list
                for tx in sent_transaction:
                    if isinstance(tx, dict):
                        self.process_sent_edges([tx], from_id, to_id)

            elif isinstance(sent_transaction, str):
                # This could be an edge label like "SENT", ignore for now
                continue

    def validate_dict_entry(self, entry: Any, entry_name: str) -> Dict[str, Any]:
        """Validates that the given entry is a dictionary."""
        if not isinstance(entry, dict):
            logger.warning(f"Invalid format for '{entry_name}': Expected dict, got {type(entry)}")
            return {}
        return entry

    def validate_list_entry(self, entry: Any, entry_name: str) -> List[Any]:
        """Validates that the given entry is a list."""
        if not isinstance(entry, list):
            logger.warning(f"Invalid format for '{entry_name}': Expected list, got {type(entry)}")
            return []
        return entry
