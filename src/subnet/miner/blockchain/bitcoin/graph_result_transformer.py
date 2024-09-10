from typing import List, Dict, Any, Set
from loguru import logger
from src.subnet.miner.blockchain import BaseGraphTransformer


class BitcoinGraphTransformer(BaseGraphTransformer):
    def __init__(self):
        self.output_data: List[Dict[str, Any]] = []
        self.node_ids: Set[str] = set()
        self.edge_ids: Set[str] = set()

    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug("Transforming result")
        self.output_data = []
        self.node_ids = set()
        self.edge_ids = set()

        # Process each entry in the result set
        for entry in result:
            self.process_entry(entry)

        return self.output_data

    def process_entry(self, entry: Dict[str, Any]) -> None:
        """
        Generic entry processor that identifies potential nodes, edges, or summary data in the entry.
        """
        logger.debug(f"Processing entry: {entry}")

        # Check if the entry is a simple key-value pair structure (summary result)
        if all(isinstance(value, (int, float, str)) for value in entry.values()):
            # Process as a summary node
            self.process_summary(entry)
        else:
            # If it's a structured entry, treat it as potential nodes or edges
            for key, value in entry.items():
                if isinstance(value, dict):
                    # If the value is a dictionary, consider it as a potential node
                    self.add_generic_node(key, value)
                elif isinstance(value, list):
                    # If the value is a list, assume it might contain relationships or complex structures
                    self.process_list(key, value)

    def process_summary(self, summary: Dict[str, Any]) -> None:
        """
        Process a summary (e.g., total_incoming, total_outgoing) and add it to the graph.
        """
        summary_id = f"summary-{len(self.output_data)}"  # Create a unique ID for each summary
        logger.info(f"Processing Summary: {summary}")

        # Add the summary as a node to the graph output
        self.output_data.append({
            "id": summary_id,
            "type": "node",
            "label": "summary",
            **summary  # Include all key-value pairs from the summary
        })

    def process_list(self, key: str, values: List[Any]) -> None:
        """
        Processes lists, which could contain relationships or complex data structures.
        """
        for item in values:
            if isinstance(item, dict):
                self.add_generic_node(key, item)

    def add_generic_node(self, key: str, node_data: Dict[str, Any]) -> None:
        """
        Generic node processing that treats any dictionary as a node.
        """
        node_id = node_data.get('id') or node_data.get('tx_id') or node_data.get('address')

        if node_id and node_id not in self.node_ids:
            self.output_data.append({
                "id": node_id,
                "type": "node",
                "label": key,  # Use the key to categorize the node
                **node_data  # Include all node attributes generically
            })
            self.node_ids.add(node_id)
            logger.debug(f"Added node: {node_id}")

        # Process potential edges within the node data (if any)
        for subkey, subvalue in node_data.items():
            if isinstance(subvalue, dict):
                self.process_sent_edge(subvalue, node_id)

    def process_sent_edge(self, edge_data: Dict[str, Any], from_id: str) -> None:
        """
        Processes any key-value pair within a node as an edge if it has the required structure.
        """
        to_id = edge_data.get('to_id') or edge_data.get('address')
        if from_id and to_id:
            edge_id = f"{from_id}-{to_id}"
            if edge_id not in self.edge_ids:
                edge_label = edge_data.get('label', 'SENT')

                self.output_data.append({
                    "id": edge_id,
                    "type": "edge",
                    "label": edge_label,
                    "from_id": from_id,
                    "to_id": to_id,
                    **edge_data  # Include all edge attributes generically
                })
                self.edge_ids.add(edge_id)

                logger.debug(f"Processed Edge: {edge_id}, Label: {edge_label}")

