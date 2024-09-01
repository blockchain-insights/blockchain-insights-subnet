from typing import List, Dict, Any, Set
from loguru import logger
from src.subnet.miner.blockchain import BaseGraphTransformer
from src.subnet.miner.blockchain.base_transformer import satoshi_to_btc


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
            self.process_transaction_entry(entry)
        return self.output_data

    def process_transaction_entry(self, entry: Dict[str, Any]) -> None:
        # Log the entry for debugging purposes
        print(f"Entry: {entry}")  # Debugging: Log entire entry

        address_node = entry.get('a1')
        recipient_node = entry.get('a2')
        transaction_node = entry.get('t1')

        # Check if nodes are not None and access properties
        address = address_node['address'] if address_node else None
        recipient = recipient_node['address'] if recipient_node else None
        transaction = transaction_node if transaction_node else {}

        tx_id = transaction.get('tx_id')

        logger.info(f"Processing Entry: address={address}, recipient={recipient}, tx_id={tx_id}")

        # Add the sender address node
        if address and address not in self.address_ids:
            self.output_data.append({
                "id": address,
                "type": "node",
                "label": "address"
            })
            self.address_ids.add(address)

        # Add the recipient address node
        if recipient and recipient not in self.address_ids:
            self.output_data.append({
                "id": recipient,
                "type": "node",
                "label": "address"
            })
            self.address_ids.add(recipient)

        # Add the transaction node
        if tx_id and tx_id not in self.transaction_ids:
            self.output_data.append({
                "id": tx_id,
                "type": "node",
                "label": "transaction",
                "balance": satoshi_to_btc(transaction.get('out_total_amount', 0)),
                "timestamp": transaction.get('timestamp'),
                "block_height": transaction.get('block_height')
            })
            self.transaction_ids.add(tx_id)

        # Process edges using the `value_satoshi`
        sent_transaction1 = entry.get('s1', {})
        sent_transaction2 = entry.get('s2', {})

        logger.debug(f"s1 value_satoshi: {sent_transaction1.get('value_satoshi')}")
        logger.debug(f"s2 value_satoshi: {sent_transaction2.get('value_satoshi')}")

        self.process_sent_edge(sent_transaction1, address, tx_id)
        self.process_sent_edge(sent_transaction2, tx_id, recipient)

    def process_sent_edge(self, sent_transaction: Dict[str, Any], from_id: str, to_id: str) -> None:
        value_satoshi = sent_transaction.get('value_satoshi')

        edge_id = f"{from_id}-{to_id}"
        if from_id and to_id and edge_id not in self.edge_ids:
            if value_satoshi is not None:
                edge_label = f"{satoshi_to_btc(value_satoshi):.8f} BTC"
            else:
                edge_label = "SENT"

            self.output_data.append({
                "id": edge_id,
                "type": "edge",
                "label": edge_label,
                "from_id": from_id,
                "to_id": to_id
            })
            self.edge_ids.add(edge_id)

            logger.debug(f"Processed Edge: {edge_id}, Label: {edge_label}")
