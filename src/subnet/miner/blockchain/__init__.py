from src.subnet.miner._config import MinerSettings
from src.subnet.miner.blockchain.base_search import BaseGraphSearch, BaseBalanceSearch
from src.subnet.miner.blockchain.bitcoin.balance_search import BitcoinBalanceSearch
from src.subnet.miner.blockchain.bitcoin.graph_search import BitcoinGraphSearch
from src.subnet.protocol import NETWORK_BITCOIN


class GraphSearchFactory:
    @classmethod
    def create_graph_search(cls, settings: MinerSettings) -> BaseGraphSearch:
        graph_search_class = {
            NETWORK_BITCOIN: BitcoinGraphSearch,
            # Add other networks and their corresponding classes as needed
        }.get(settings.NETWORK)

        if graph_search_class is None:
            raise ValueError(f"Unsupported network Type: {settings.NETWORK}")

        return graph_search_class(settings)


class BalanceSearchFactory:
    @classmethod
    def create_balance_search(cls, network: str) -> BaseBalanceSearch:
        graph_search_class = {
            NETWORK_BITCOIN: BitcoinBalanceSearch,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if graph_search_class is None:
            raise ValueError(f"Unsupported network Type: {network}")

        return graph_search_class()
