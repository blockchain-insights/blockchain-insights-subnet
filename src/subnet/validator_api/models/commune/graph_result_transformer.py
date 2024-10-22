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
        self.output_data.clear()
        self.transaction_ids.clear()
        self.address_ids.clear()
        self.edge_ids.clear()

    def process_entry(self, entry: Dict[str, Any]) -> None:
        self.process_address_nodes(entry)
        self.process_transaction_nodes(entry)
        self.process_sent_edges(entry)

    def process_address_nodes(self, entry: Dict[str, Any]) -> None:
        for key, value in entry.items():
            if key.startswith("a") and value:
                address_id = value["id"]
                address = value["properties"].get("address")

                if address_id not in self.address_ids:
                    self.output_data.append({
                        "id": address_id,
                        "type": "node",
                        "label": "address",
                        "address": address,
                    })
                    self.address_ids.add(address_id)

    def process_transaction_nodes(self, entry: Dict[str, Any]) -> None:
        for key, value in entry.items():
            if key.startswith("t") and value:
                tx_id = value["properties"].get("tx_id")

                if tx_id not in self.transaction_ids:
                    self.output_data.append({
                        "id": tx_id,
                        "type": "node",
                        "label": "transaction",
                        "balance": satoshi_to_btc(value["properties"].get("out_total_amount", 0)),
                        "timestamp": value["properties"].get("timestamp"),
                        "block_height": value["properties"].get("block_height"),
                    })
                    self.transaction_ids.add(tx_id)

    def process_sent_edges(self, entry: Dict[str, Any]) -> None:
        for key, value in entry.items():
            if key.startswith("s") and value:
                edge_data = self._generate_edge_data(entry, value)
                self.output_data.append(edge_data)

    def _generate_edge_data(self, entry: Dict[str, Any], value: Dict[str, Any]) -> Dict[str, Any]:
        from_id = value["start"]
        to_id = value["end"]
        value_satoshi = value["properties"].get("value_satoshi")

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
