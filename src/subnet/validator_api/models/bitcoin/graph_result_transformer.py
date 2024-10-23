from typing import List, Dict, Any, Set
from loguru import logger
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc

class BitcoinGraphTransformer(BaseGraphTransformer):
    def __init__(self):
        self.output_data: List[Dict[str, Any]] = []
        self.transaction_ids: Set[str] = set()
        self.addresses: Set[str] = set()
        self.edge_ids: Set[str] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug("Transforming result for Bitcoin")
        self._reset_state()

        for entry in result:
            try:
                self.process_entry(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}, Entry: {entry}")

        return self.output_data

    def _reset_state(self):
        """Reset state between transformations."""
        self.output_data.clear()
        self.transaction_ids.clear()
        self.addresses.clear()
        self.edge_ids.clear()

    def process_entry(self, entry: Dict[str, Any]) -> None:
        """Process each entry, handling transactions, addresses, and sent edges."""
        if "t1" in entry:
            self.process_transaction(entry["t1"])
        if "a3" in entry:
            self.process_addresses(entry["a3"])
        if "a4" in entry:
            self.process_addresses(entry["a4"])
        if "s3" in entry:
            self.process_sent_edges(entry["s3"])

    def process_transaction(self, transaction: Dict[str, Any]) -> None:
        """Process and store transaction nodes."""
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

    def process_addresses(self, addresses: List[Dict[str, Any]]) -> None:
        """Process and store address nodes."""
        for address_entry in addresses:
            address = address_entry.get("address")

            if address and address not in self.addresses:
                self.output_data.append({
                    "id": address,
                    "type": "node",
                    "label": "address",
                    "address": address,
                })
                self.addresses.add(address)

    def process_sent_edges(self, edges: List[Dict[str, Any]]) -> None:
        """Process and store SENT edges."""
        for edge in edges:
            edge_data = self._generate_edge_data(edge)
            if edge_data["id"] not in self.edge_ids:
                self.output_data.append(edge_data)
                self.edge_ids.add(edge_data["id"])

    def _generate_edge_data(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured edge data."""
        from_id = edge["start"]
        to_id = edge["end"]
        value_satoshi = edge.get("value_satoshi", 0)

        edge_id = f"{from_id}-{to_id}"
        return {
            "id": edge_id,
            "type": "edge",
            "label": f"{satoshi_to_btc(value_satoshi):.8f} BTC",
            "from_id": from_id,
            "to_id": to_id,
            "satoshi_value": value_satoshi,
            "btc_value": satoshi_to_btc(value_satoshi),
        }
