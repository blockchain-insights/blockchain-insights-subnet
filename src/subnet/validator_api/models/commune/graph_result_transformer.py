from typing import List, Dict, Any, Set
from loguru import logger
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc

class CommuneGraphTransformer(BaseGraphTransformer):
    def __init__(self):
        self.output_data: List[Dict[str, Any]] = []
        self.transaction_ids: Set[str] = set()
        self.address_ids: Set[str] = set()
        self.edge_ids: Set[str] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug("Transforming result for Commune")
        self._reset_state()

        for entry in result:
            try:
                self.process_entry(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}, Entry: {entry}")

        return self.output_data

    def _reset_state(self):
        """Reset the state between transformations to avoid duplication."""
        self.output_data.clear()
        self.transaction_ids.clear()
        self.address_ids.clear()
        self.edge_ids.clear()

    def process_entry(self, entry: Dict[str, Any]) -> None:
        """Process transactions, addresses, and sent edges."""
        self.process_address_nodes(entry.get("a3", []))
        self.process_address_nodes(entry.get("a4", []))
        self.process_transaction_node(entry.get("t1"))
        self.process_transactions(entry.get("t2", []))
        self.process_transactions(entry.get("t3", []))
        self.process_sent_edges(entry.get("s3", []))

    def process_address_nodes(self, addresses: List[Dict[str, Any]]) -> None:
        """Handle address nodes to avoid duplicates."""
        for address_entry in addresses:
            address = address_entry.get("address")

            if address and address not in self.address_ids:
                self.output_data.append({
                    "id": address,
                    "type": "node",
                    "label": "address",
                    "address": address,
                })
                self.address_ids.add(address)

    def process_transaction_node(self, transaction: Dict[str, Any]) -> None:
        """Process a single transaction node."""
        if transaction:
            tx_id = transaction["properties"]["tx_id"]

            if tx_id not in self.transaction_ids:
                self.output_data.append({
                    "id": tx_id,
                    "type": "node",
                    "label": "transaction",
                    "balance": satoshi_to_btc(transaction["properties"].get("out_total_amount", 0)),
                    "timestamp": transaction["properties"].get("timestamp"),
                    "block_height": transaction["properties"].get("block_height"),
                })
                self.transaction_ids.add(tx_id)

    def process_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        """Process a list of transactions."""
        for tx in transactions:
            self.process_transaction_node(tx)

    def process_sent_edges(self, edges: List[Dict[str, Any]]) -> None:
        """Process sent edges and store them."""
        for edge in edges:
            edge_data = self._generate_edge_data(edge)
            if edge_data["id"] not in self.edge_ids:
                self.output_data.append(edge_data)
                self.edge_ids.add(edge_data["id"])

    def _generate_edge_data(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """Generate edge data for output."""
        from_id = edge["start"]
        to_id = edge["end"]
        value_satoshi = edge.get("value_satoshi", 0)

        edge_id = f"{from_id}-{to_id}"
        return {
            "id": edge_id,
            "type": "edge",
            "label": f"{satoshi_to_btc(value_satoshi):.8f} comai",
            "from_id": from_id,
            "to_id": to_id,
            "satoshi_value": value_satoshi,
            "comai_value": satoshi_to_btc(value_satoshi),
        }
