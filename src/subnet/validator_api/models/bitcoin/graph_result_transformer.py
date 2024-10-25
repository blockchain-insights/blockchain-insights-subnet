from typing import List, Dict, Any, Set, Tuple
from loguru import logger
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc

class BitcoinGraphTransformer(BaseGraphTransformer):
    def __init__(self):
        self.output_data: List[Dict[str, Any]] = []
        self.transaction_ids: Set[str] = set()
        self.address_ids: Set[str] = set()
        self.edge_ids: Set[Tuple[str, str]] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform the result to extract nodes and edges."""
        logger.debug("Transforming result for Bitcoin")
        self._reset_state()

        for entry in result:
            try:
                if "path1" in entry or "path2" in entry:
                    self.process_path_entry(entry)  # Process paths
                else:
                    self.process_entry(entry)  # Process non-path entries
            except Exception as e:
                logger.error(f"Error processing entry: {e}, Entry: {entry}")

        return self.output_data

    def _reset_state(self):
        """Reset internal state to avoid duplicate processing."""
        self.output_data.clear()
        self.transaction_ids.clear()
        self.address_ids.clear()
        self.edge_ids.clear()

    # ========== Non-Path Handling Logic (Preserved) ==========

    def process_entry(self, entry: Dict[str, Any]) -> None:
        """Process non-path entries."""
        self.process_address_nodes(entry)
        self.process_transaction_nodes(entry)
        self.process_sent_edges(entry)

    def process_address_nodes(self, entry: Dict[str, Any]) -> None:
        """Extract and add address nodes."""
        for key, value in entry.items():
            if key.startswith("a") and value:
                address = value["properties"].get("address")
                if address and address not in self.address_ids:
                    self.output_data.append({
                        "id": address,
                        "type": "node",
                        "label": "address",
                        "address": address,
                    })
                    self.address_ids.add(address)

    def process_transaction_nodes(self, entry: Dict[str, Any]) -> None:
        """Extract and add transaction nodes."""
        for key, value in entry.items():
            if key.startswith("t") and value:
                tx_id = value["properties"].get("tx_id")
                if tx_id and tx_id not in self.transaction_ids:
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
        """Extract SENT edges and prevent duplicates."""
        for key, value in entry.items():
            if key.startswith("s") and value:
                edge_data = self._generate_edge_data(entry, value)
                if edge_data:
                    self.output_data.append(edge_data)

    def _generate_edge_data(self, entry: Dict[str, Any], edge: Dict[str, Any]) -> Dict[str, Any]:
        """Generate edge data with proper ID and values."""
        from_value, _ = self._get_actual_node_value(edge["start"], entry)
        to_value, _ = self._get_actual_node_value(edge["end"], entry)
        value_satoshi = edge["properties"].get("value_satoshi", 0)

        edge_id = f"{from_value}-{to_value}"

        if (from_value, to_value) in self.edge_ids:
            return None  # Avoid duplicate edges
        self.edge_ids.add((from_value, to_value))

        return {
            "id": edge_id,
            "type": "edge",
            "label": f"{satoshi_to_btc(value_satoshi):.8f} BTC",
            "from_id": from_value,
            "to_id": to_value,
            "satoshi_value": value_satoshi,
            "btc_value": satoshi_to_btc(value_satoshi),
        }

    def _get_actual_node_value(self, node_id: int, entry: Dict[str, Any]) -> Tuple[str, str]:
        """Extract address or transaction ID based on the node type."""
        for key, value in entry.items():
            if key.startswith("a") and value["id"] == node_id:
                return value["properties"]["address"], "address"
            elif key.startswith("t") and value["id"] == node_id:
                return value["properties"]["tx_id"], "transaction"
        return str(node_id), "unknown"

    # ========== Path Handling Logic (Updated) ==========

    def process_path_entry(self, entry: Dict[str, Any]) -> None:
        """Process path-based entries."""
        for path_key in ["path1", "path2"]:
            if path_key in entry:
                path_data = entry[path_key]
                nodes = path_data.get("_nodes", [])
                relationships = path_data.get("_relationships", [])

                self._process_path_nodes(nodes)
                self._process_path_relationships(nodes, relationships)

    def _process_path_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Extract nodes from paths."""
        for node in nodes:
            if "address" in node:
                self._add_address_node(node)
            elif "tx_id" in node:
                self._add_transaction_node(node)

    def _process_path_relationships(self, nodes: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> None:
        """Extract relationships (edges) from paths."""
        # Loop through each relationship and the corresponding node pairs
        for i, relationship in enumerate(relationships):
            if i + 1 < len(nodes):
                from_node = nodes[i]
                to_node = nodes[i + 1]
                value_satoshi = relationship.get("value_satoshi", 0)
                self._add_path_edge(from_node, to_node, value_satoshi)

    def _add_address_node(self, node: Dict[str, Any]) -> None:
        """Add an address node."""
        address = node["address"]
        if address not in self.address_ids:
            self.output_data.append({
                "id": address,
                "type": "node",
                "label": "address",
                "address": address,
            })
            self.address_ids.add(address)

    def _add_transaction_node(self, node: Dict[str, Any]) -> None:
        """Add a transaction node."""
        tx_id = node["tx_id"]
        if tx_id not in self.transaction_ids:
            self.output_data.append({
                "id": tx_id,
                "type": "node",
                "label": "transaction",
                "balance": satoshi_to_btc(node.get("out_total_amount", 0)),
                "timestamp": node.get("timestamp"),
                "block_height": node.get("block_height"),
            })
            self.transaction_ids.add(tx_id)

    def _add_path_edge(self, from_node: Dict[str, Any], to_node: Dict[str, Any], value_satoshi: int) -> None:
        """Add an edge for path-based entries."""
        from_id = from_node.get("address") or from_node.get("tx_id")
        to_id = to_node.get("address") or to_node.get("tx_id")
        edge_id = f"{from_id}-{to_id}"

        if (from_id, to_id) in self.edge_ids:
            return  # Avoid duplicate edges
        self.edge_ids.add((from_id, to_id))

        self.output_data.append({
            "id": edge_id,
            "type": "edge",
            "label": f"{satoshi_to_btc(value_satoshi):.8f} BTC",
            "from_id": from_id,
            "to_id": to_id,
            "satoshi_value": value_satoshi,
            "btc_value": satoshi_to_btc(value_satoshi),
        })
