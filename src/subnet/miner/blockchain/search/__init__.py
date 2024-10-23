from src.subnet.miner._config import MinerSettings
from src.subnet.miner.blockchain import GraphSearch, BalanceSearch
from src.subnet.miner.blockchain.search.utxo_graph_search import UtxoGraphSearch
from src.subnet.protocol import NETWORK_COMMUNE, NETWORK_BITCOIN


class GraphSearchFactory:
    @classmethod
    def create_graph_search(cls, settings: MinerSettings) -> GraphSearch:
        graph_search_class = {
            NETWORK_BITCOIN: UtxoGraphSearch,
            NETWORK_COMMUNE: UtxoGraphSearch
            # Add other networks and their corresponding classes as needed
        }.get(settings.NETWORK)

        if graph_search_class is None:
            raise ValueError(f"Unsupported network Type: {settings.NETWORK}")

        return graph_search_class(settings)


class BalanceSearchFactory:
    @classmethod
    def create_balance_search(cls, network: str) -> BalanceSearch:
        graph_search_class = {
            NETWORK_BITCOIN: BalanceSearch,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if graph_search_class is None:
            raise ValueError(f"Unsupported network Type: {network}")

        return graph_search_class()
