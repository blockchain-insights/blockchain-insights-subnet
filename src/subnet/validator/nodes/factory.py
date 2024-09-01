from src.subnet.protocol.blockchain import NETWORK_BITCOIN
from src.subnet.validator.nodes.bitcoin.node import BitcoinNode


class NodeFactory:
    @classmethod
    def create_node(cls, network: str):
        node_class = {
            NETWORK_BITCOIN: BitcoinNode,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if node_class is None:
            raise ValueError(f"Unsupported network: {network}")

        return node_class()