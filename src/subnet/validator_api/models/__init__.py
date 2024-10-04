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


# Helper function to convert satoshi to BTC
def satoshi_to_btc(satoshi: int) -> float:
    return satoshi / 1e8


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

        address_node = entry.get('a1')
        recipient_node = entry.get('a2')
        transaction_node = entry.get('t1')

        # Ensure the nodes are dictionaries
        if not isinstance(address_node, dict):
            logger.warning(f"Invalid format for 'a1': {address_node}")
            address_node = {}
        if not isinstance(recipient_node, dict):
            logger.warning(f"Invalid format for 'a2': {recipient_node}")
            recipient_node = {}
        if not isinstance(transaction_node, dict):
            logger.warning(f"Invalid format for 't1': {transaction_node}")
            transaction_node = {}

        address = address_node.get('address')
        recipient = recipient_node.get('address')
        tx_id = transaction_node.get('tx_id')

        logger.debug(f"address={address}, recipient={recipient}, tx_id={tx_id}")

        # Add sender address node
        if address and address not in self.address_ids:
            self.output_data.append({
                "id": address,
                "type": "node",
                "label": "address"
            })
            self.address_ids.add(address)

        # Add recipient address node
        if recipient and recipient not in self.address_ids:
            self.output_data.append({
                "id": recipient,
                "type": "node",
                "label": "address"
            })
            self.address_ids.add(recipient)

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

        # Process edges using the `value_satoshi`
        sent_transaction1 = entry.get('s1', {})
        sent_transaction2 = entry.get('s2', {})

        self.process_sent_edge(sent_transaction1, address, tx_id)
        self.process_sent_edge(sent_transaction2, tx_id, recipient)

    def process_sent_edge(self, sent_transaction: Any, from_id: str, to_id: str) -> None:
        if not isinstance(sent_transaction, dict):
            logger.warning(f"Invalid format for sent transaction: {sent_transaction}")
            sent_transaction = {}

        value_satoshi = sent_transaction.get('value_satoshi')

        edge_id = f"{from_id}-{to_id}"
        if from_id and to_id and edge_id not in self.edge_ids:
            edge_label = f"{satoshi_to_btc(value_satoshi):.8f} BTC" if value_satoshi else "SENT"

            self.output_data.append({
                "id": edge_id,
                "type": "edge",
                "label": edge_label,
                "from_id": from_id,
                "to_id": to_id
            })
            self.edge_ids.add(edge_id)

            logger.debug(f"Processed Edge: {edge_id}, Label: {edge_label}")
            logger.debug(f"Processed Edge: {edge_id}, Label: {edge_label}")  # Debugging: Log edge creation