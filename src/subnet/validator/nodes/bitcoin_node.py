from bitcoin.rpc import Proxy
from loguru import logger
from src.subnet.validator.nodes.abstract_node import Node


class BitcoinNode(Node):
    def __init__(self, node_rpc_url):
        self.node_rpc_url = node_rpc_url
        super().__init__()

    def get_current_block_height(self):
        proxy = Proxy(service_url=self.node_rpc_url)
        try:
            result = proxy.getblockcount()
            return result
        except Exception as e:
            logger.error(f"RPC Provider with Error", error=str(e))
        finally:
            proxy.close()
