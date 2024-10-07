from abc import ABC, abstractmethod
from typing import List, Any, Dict, Set

from loguru import logger


def satoshi_to_btc(satoshi: int) -> float:
    return satoshi / 1e8


class BaseGraphTransformer(ABC):
    @abstractmethod
    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform graph results into a structured format."""
        pass


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

        # Extract and validate nodes (addresses and transaction)
        address_node = self.validate_dict_entry(entry.get('a1'), 'a1')
        recipient_node = self.validate_dict_entry(entry.get('a2'), 'a2')
        transaction_node = self.validate_dict_entry(entry.get('t1'), 't1')

        if not transaction_node:
            logger.warning("Skipping entry due to missing transaction node (t1).")
            return

        tx_id = transaction_node.get('tx_id')

        # Add transaction node
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

        # Add address nodes (a1 and a2)
        self.add_address_node(address_node, 'address')
        self.add_address_node(recipient_node, 'recipient')

        address = address_node.get('address')
        recipient = recipient_node.get('address')

        # Process edges from sender to transaction and from transaction to recipient
        sent_transactions1 = self.validate_list_entry(entry.get('s1'), 's1')
        sent_transactions2 = self.validate_list_entry(entry.get('s2'), 's2')

        self.process_sent_edges(sent_transactions1, address, tx_id)
        self.process_sent_edges(sent_transactions2, tx_id, recipient)

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
        if not sent_transactions:
            logger.warning(f"Skipping edge creation due to invalid sent transactions.")
            return

        edge_label = "SENT"  # Default edge label

        for sent_transaction in sent_transactions:
            if isinstance(sent_transaction, dict):
                block_height = sent_transaction.get('block_height')
                tx_id = sent_transaction.get('tx_id')
                value_satoshi = sent_transaction.get('out_total_amount')

                edge_id = f"{from_id}-{to_id}"
                if from_id and to_id and edge_id not in self.edge_ids:
                    edge_label = f"{satoshi_to_btc(value_satoshi):.8f} BTC" if value_satoshi else edge_label

                    self.output_data.append({
                        "id": edge_id,
                        "type": "edge",
                        "label": edge_label,
                        "from_id": from_id,
                        "to_id": to_id,
                        "block_height": block_height,
                        "tx_id": tx_id
                    })
                    self.edge_ids.add(edge_id)

                    logger.debug(f"Processed Edge: {edge_id}, Label: {edge_label}, Block: {block_height}, Tx: {tx_id}")
            elif isinstance(sent_transaction, str):
                # Update the label if a string like 'SENT' is encountered
                edge_label = sent_transaction
            else:
                logger.warning(f"Invalid transaction type: {sent_transaction}")

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
