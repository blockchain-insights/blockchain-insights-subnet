from typing import List, Dict, Any, Set, Tuple, Optional
from loguru import logger
from src.subnet.validator_api.models import BaseGraphTransformer, satoshi_to_btc

class CommuneGraphTransformer(BaseGraphTransformer):
    def __init__(self):
        self.output_data: List[Dict[str, Any]] = []
        self.transaction_ids: Set[str] = set()
        self.address_ids: Set[str] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform the result to extract paths, addresses, and transactions."""
        logger.debug("Transforming result for Comai")
        self._reset_state()

        for entry in result:
            try:
                # Handle entries with paths (path1, path2).
                if "path1" in entry or "path2" in entry:
                    self._process_path_entry(entry)
                # Handle standard entries with variable nodes.
                else:
                    self._process_standard_entry(entry)
            except Exception as e:
                logger.error(f"Error processing entry: {e}, Entry: {entry}")

        return self.output_data

    def _reset_state(self):
        """Reset internal state to avoid duplicate processing."""
        self.output_data.clear()
        self.transaction_ids.clear()
        self.address_ids.clear()

    # ========== Standard Entry Handling Logic ==========

    def _process_standard_entry(self, entry: Dict[str, Any]) -> None:
        """Dynamically process address and transaction nodes."""
        for key, value in entry.items():
            if key.startswith("a") and value:
                self._process_address(entry, key)
            elif key.startswith("t") and value:
                self._process_transaction(entry, key)

    def _process_address(self, entry: Dict[str, Any], key: str) -> None:
        """Extract and add address nodes."""
        address_data = entry[key]["properties"]
        address = address_data.get("address")

        if address and address not in self.address_ids:
            self.output_data.append({
                "id": address,
                "type": "node",
                "label": "address",
                "address": address,
            })
            self.address_ids.add(address)

    def _process_transaction(self, entry: Dict[str, Any], key: str) -> None:
        """Extract and add transaction nodes with linked addresses."""
        transaction = entry[key]
        tx_properties = transaction["properties"]
        tx_id = tx_properties.get("id")
        amount = tx_properties.get("amount", 0)
        block_height = tx_properties.get("block_height")
        timestamp = self._format_timestamp(tx_properties.get("timestamp"))

        from_address = self._get_address_by_id(entry, transaction["start"])
        to_address = self._get_address_by_id(entry, transaction["end"])

        if tx_id and tx_id not in self.transaction_ids:
            self.output_data.append({
                "id": tx_id,
                "type": "transaction",
                "label": "transaction",
                "amount": satoshi_to_btc(amount),
                "block_height": block_height,
                "timestamp": timestamp,
                "from_address": from_address,
                "to_address": to_address,
            })
            self.transaction_ids.add(tx_id)

    # ========== Path Handling Logic ==========

    def _process_path_entry(self, entry: Dict[str, Any]) -> None:
        """Process entries with paths."""
        for path_key in ["path1", "path2"]:
            if path_key in entry and entry[path_key]:
                path_data = entry[path_key]
                nodes = path_data.get("_nodes", [])
                relationships = path_data.get("_relationships", [])

                self._process_path_nodes(nodes)
                self._process_path_relationships(nodes, relationships)

    def _process_path_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Extract and add address nodes from paths."""
        for node in nodes:
            address = node.get("address")
            if address and address not in self.address_ids:
                self.output_data.append({
                    "id": address,
                    "type": "node",
                    "label": "address",
                    "address": address,
                })
                self.address_ids.add(address)

    def _process_path_relationships(self, nodes: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> None:
        """Extract and add transactions from path relationships."""
        for i, relationship in enumerate(relationships):
            from_address = nodes[i].get("address") if i < len(nodes) else "unknown"
            to_address = nodes[i + 1].get("address") if (i + 1) < len(nodes) else "unknown"
            self._add_transaction(relationship, from_address, to_address)

    def _add_transaction(self, relationship: Dict[str, Any], from_address: str, to_address: str) -> None:
        """Add a transaction with linked addresses."""
        tx_id = relationship.get("id")
        amount = relationship.get("amount", 0)
        block_height = relationship.get("block_height")
        timestamp = self._format_timestamp(relationship.get("timestamp"))

        if tx_id and tx_id not in self.transaction_ids:
            self.output_data.append({
                "id": tx_id,
                "type": "transaction",
                "label": "transaction",
                "amount": satoshi_to_btc(amount),
                "block_height": block_height,
                "timestamp": timestamp,
                "from_address": from_address,
                "to_address": to_address,
            })
            self.transaction_ids.add(tx_id)

    # ========== Helper Functions ==========

    def _format_timestamp(self, timestamp_obj: Dict[str, Any]) -> Optional[str]:
        """Convert timestamp to 'YYYY-MM-DD HH:MM:SS' format."""
        if not timestamp_obj:
            return None

        date = timestamp_obj.get('_DateTime__date', {})
        time = timestamp_obj.get('_DateTime__time', {})

        year = date.get('_Date__year', 1970)
        month = date.get('_Date__month', 1)
        day = date.get('_Date__day', 1)
        hour = time.get('_Time__hour', 0)
        minute = time.get('_Time__minute', 0)
        second = time.get('_Time__second', 0)

        return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

    def _get_address_by_id(self, entry: Dict[str, Any], address_id: int) -> str:
        """Retrieve address by ID from the entry."""
        for key, value in entry.items():
            if key.startswith("a") and value["id"] == address_id:
                return value["properties"].get("address", "unknown")
        return "unknown"
