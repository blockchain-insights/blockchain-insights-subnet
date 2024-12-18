from substrateinterface import SubstrateInterface
from src.subnet.validator.nodes.abstract_node import Node


class CommuneNode(Node):
    def __init__(self, node_rpc_url: str):
        super().__init__()
        self.substrate = SubstrateInterface(
            url=node_rpc_url,
            ss58_format=0,
        )

    def get_current_block_height(self):
        header = self.substrate.get_block_header()
        return header['header']['number']
