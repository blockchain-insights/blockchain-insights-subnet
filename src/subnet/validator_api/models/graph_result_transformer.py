from typing import List, Dict, Any, Set
from loguru import logger
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc

class GraphTransformer(BaseGraphTransformer):
    def __init__(self, network: str):
        self.network = network  # Configure network (e.g., "bitcoin" or "commune")
        self.output_data: List[Dict[str, Any]] = []
        self.transaction_ids: Set[str] = set()
        self.address_ids: Set[str] = set()
        self.edge_ids: Set[str] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug(f"Transforming result for network: {self.network}")
        self.output_data.clear()
        self.transaction_ids.clear()
        self.address_ids.clear()
        self.edge_ids.clear()

        for entry in result:
            try:
                self.process_entry(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}, Entry: {entry}")

        return self.output_data

    def process_entry(self, entry: Dict[str, Any]) -> None:
        logger.debug(f"Processing Entry for {self.network}: {entry}")
        self.process_address_nodes(entry)
        self.process_transaction_nodes(entry)
        self.process_sent_edges(entry)

    def process_address_nodes(self, entry: Dict[str, Any]) -> None:
        """Add all address nodes to the output."""
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
        """Add all transaction nodes to the output."""
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
        """Add SENT edges with proper IDs."""
        for key, value in entry.items():
            if key.startswith("s") and value:
                from_id = value["start"]
                to_id = value["end"]
                value_satoshi = value["properties"].get("value_satoshi")

                from_node = self.get_node_by_id(entry, from_id)
                to_node = self.get_node_by_id(entry, to_id)

                # Create unique edge ID based on node types
                if from_node["type"] == "address" and to_node["type"] == "transaction":
                    edge_id = f"{from_node['address']}-{to_node['id']}"
                elif from_node["type"] == "transaction" and to_node["type"] == "address":
                    edge_id = f"{from_node['id']}-{to_node['address']}"
                else:
                    edge_id = f"{from_id}-{to_id}"

                if edge_id not in self.edge_ids:
                    edge_data = {
                        "id": edge_id,
                        "type": "edge",
                        "label": f"{satoshi_to_btc(value_satoshi):.8f} comai",  # Use "comai"
                        "from_id": from_id,
                        "to_id": to_id,
                        "satoshi_value": value_satoshi,
                    }

                    # Add appropriate currency field based on network
                    if self.network == "bitcoin":
                        edge_data["btc_value"] = satoshi_to_btc(value_satoshi)
                    elif self.network == "commune":
                        edge_data["comai_value"] = satoshi_to_btc(value_satoshi)

                    self.output_data.append(edge_data)
                    self.edge_ids.add(edge_id)

    def get_node_by_id(self, entry: Dict[str, Any], node_id: Any) -> Dict[str, Any]:
        """Helper to retrieve a node by ID."""
        for key, value in entry.items():
            if value and value["id"] == node_id:
                if key.startswith("a"):
                    return {"type": "address", "address": value["properties"]["address"]}
                if key.startswith("t"):
                    return {"type": "transaction", "id": value["properties"]["tx_id"]}
        return {"type": "unknown", "id": node_id}
