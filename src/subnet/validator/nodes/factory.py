from src.subnet.protocol import NETWORK_BITCOIN, NETWORK_COMMUNE
from src.subnet.validator.nodes.bitcoin_node import BitcoinNode
from src.subnet.validator.nodes.commune_node import CommuneNode


class NodeFactory:
    @classmethod
    def create_node(cls, node_rpc_urls: dict, network: str):
        node_class = {
            NETWORK_BITCOIN: BitcoinNode,
            NETWORK_COMMUNE: CommuneNode,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if node_class is None:
            raise ValueError(f"Unsupported network: {network}")

        return node_class(node_rpc_urls[network])
