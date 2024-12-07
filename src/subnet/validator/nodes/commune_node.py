from substrateinterface import SubstrateInterface
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.nodes.abstract_node import Node


class CommuneNode(Node):
    def __init__(self, settings: ValidatorSettings):
        super().__init__()
        self.setting = settings
        self.substrate = SubstrateInterface(
            url=settings.COMMUNE_NODE_RPC,
            ss58_format=0,
        )

    def get_current_block_height(self):
        header = self.substrate.get_block_header()
        return header['header']['number']
