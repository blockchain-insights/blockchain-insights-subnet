from typing import List, Dict, Any, Set
from loguru import logger
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc

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

        # Extract nodes and relationships from the entry
        address_node = self.validate_dict_entry(entry.get('a1'), 'a1')
        recipient_node = self.validate_dict_entry(entry.get('a2'), 'a2')
        transaction_node = self.validate_dict_entry(entry.get('t1'), 't1')

        sent_edge1 = self.validate_dict_entry(entry.get('s1'), 's1')
        sent_edge2 = self.validate_dict_entry(entry.get('s2'), 's2')

        # Process the nodes and edges if valid
        if transaction_node:
            self.process_transaction_node(transaction_node)

        self.add_address_node(address_node, 'address')
        self.add_address_node(recipient_node, 'recipient')

        address = address_node.get('properties', {}).get('address')
        recipient = recipient_node.get('properties', {}).get('address')

        # Process the SENT edges
        self.process_sent_edge(sent_edge1, address, transaction_node.get('properties', {}).get('tx_id'))
        self.process_sent_edge(sent_edge2, transaction_node.get('properties', {}).get('tx_id'), recipient)

    def process_transaction_node(self, transaction_node: Dict[str, Any]) -> None:
        tx_id = transaction_node.get('properties', {}).get('tx_id')

        if tx_id and tx_id not in self.transaction_ids:
            self.output_data.append({
                "id": tx_id,
                "type": "node",
                "label": "transaction",
                "balance": satoshi_to_btc(transaction_node['properties'].get('out_total_amount', 0)),
                "timestamp": transaction_node['properties'].get('timestamp'),
                "block_height": transaction_node['properties'].get('block_height')
            })
            self.transaction_ids.add(tx_id)

    def add_address_node(self, address_node: Dict[str, Any], label: str) -> None:
        address = address_node.get('properties', {}).get('address')

        if address and address not in self.address_ids:
            self.output_data.append({
                "id": address,
                "type": "node",
                "label": label,
                "name": address_node['properties'].get('address')
            })
            self.address_ids.add(address)

    def process_sent_edge(self, sent_edge: Dict[str, Any], from_id: str, to_id: str) -> None:
        if not sent_edge:
            logger.warning("Skipping invalid sent edge.")
            return

        edge_id = f"{from_id}-{to_id}"
        if edge_id not in self.edge_ids:
            value_satoshi = sent_edge['properties'].get('value_satoshi')
            edge_label = f"{satoshi_to_btc(value_satoshi):.8f} BTC" if value_satoshi else "SENT"

            self.output_data.append({
                "id": edge_id,
                "type": "edge",
                "label": edge_label,
                "from_id": from_id,
                "to_id": to_id,
                "block_height": sent_edge['properties'].get('block_height'),
                "tx_id": sent_edge['properties'].get('tx_id'),
                "satoshi_value": value_satoshi,
                "btc_value": satoshi_to_btc(value_satoshi)
            })
            self.edge_ids.add(edge_id)

    def validate_dict_entry(self, entry: Any, entry_name: str) -> Dict[str, Any]:
        """Ensures the entry is a valid dictionary."""
        if not isinstance(entry, dict):
            logger.warning(f"Invalid format for '{entry_name}': Expected dict, got {type(entry)}")
            return {}
        return entry
