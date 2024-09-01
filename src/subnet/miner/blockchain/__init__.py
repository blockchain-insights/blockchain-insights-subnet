from sqlalchemy.ext.asyncio import AsyncSession
from src.subnet.miner._config import MinerSettings
from src.subnet.miner.blockchain.base_search import BaseGraphSearch, BaseBalanceSearch
from src.subnet.miner.blockchain.base_transformer import BaseGraphTransformer, BaseChartTransformer, \
    BaseTabularTransformer, BaseGraphSummaryTransformer
from src.subnet.miner.blockchain.bitcoin.balance_search import BitcoinBalanceSearch
from src.subnet.miner.blockchain.bitcoin.chart_result_transformer import BitcoinChartTransformer
from src.subnet.miner.blockchain.bitcoin.graph_result_transformer import BitcoinGraphTransformer
from src.subnet.miner.blockchain.bitcoin.graph_search import BitcoinGraphSearch
from src.subnet.miner.blockchain.bitcoin.graph_summary_transformer import BitcoinGraphSummaryTransformer
from src.subnet.miner.blockchain.bitcoin.tabular_result_transformer import BitcoinTabularTransformer
from src.subnet.protocol.blockchain import NETWORK_BITCOIN


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


class GraphTransformerFactory:
    @classmethod
    def create_graph_transformer(cls, network: str) -> BaseGraphTransformer:
        transformer_class = {
            NETWORK_BITCOIN: BitcoinGraphTransformer,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if transformer_class is None:
            raise ValueError(f"Unsupported network type: {network}")

        return transformer_class()


class ChartTransformerFactory:
    @classmethod
    def create_chart_transformer(cls, network: str) -> BaseChartTransformer:
        transformer_class = {
            NETWORK_BITCOIN: BitcoinChartTransformer,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if transformer_class is None:
            raise ValueError(f"Unsupported network type: {network}")

        return transformer_class()


class TabularTransformerFactory:
    @classmethod
    def create_tabular_transformer(cls, network: str) -> BaseTabularTransformer:
        transformer_class = {
            NETWORK_BITCOIN: BitcoinTabularTransformer,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if transformer_class is None:
            raise ValueError(f"Unsupported network type: {network}")

        return transformer_class()


class GraphSummaryTransformerFactory:
    @classmethod
    def create_graph_summary_transformer(cls, network: str) -> BaseGraphSummaryTransformer:
        transformer_class = {
            NETWORK_BITCOIN: BitcoinGraphSummaryTransformer,
            # Add other networks and their corresponding classes as needed
        }.get(network)

        if transformer_class is None:
            raise ValueError(f"Unsupported network type: {network}")

        return transformer_class()