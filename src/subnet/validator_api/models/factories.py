from src.subnet.validator_api.models.bitcoin.graph_result_transformer import BitcoinGraphTransformer
from src.subnet.validator_api.models.commune.graph_result_transformer import CommuneGraphTransformer
from src.subnet.validator_api.models.bitcoin.tabular_result_transformer import BitcoinTabularTransformer
from src.subnet.validator_api.models.commune.tabular_result_transformer import CommuneTabularTransformer
from src.subnet.validator_api.models.bitcoin.chart_result_transformer import BitcoinChartTransformer
from src.subnet.validator_api.models.commune.chart_result_transformer import CommuneChartTransformer
from typing import Union

def get_graph_transformer(network: str) -> Union[BitcoinGraphTransformer, CommuneGraphTransformer]:
    if network == "bitcoin":
        return BitcoinGraphTransformer()
    elif network == "commune":
        return CommuneGraphTransformer()
    else:
        raise ValueError(f"Unsupported network: {network}")

def get_tabular_transformer(network: str) -> Union[BitcoinTabularTransformer, CommuneTabularTransformer]:
    if network == "bitcoin":
        return BitcoinTabularTransformer()
    elif network == "commune":
        return CommuneTabularTransformer()
    else:
        raise ValueError(f"Unsupported network: {network}")

def get_chart_transformer(network: str) -> Union[BitcoinChartTransformer, CommuneChartTransformer]:
    if network == "bitcoin":
        return BitcoinChartTransformer()
    elif network == "commune":
        return CommuneChartTransformer()
    else:
        raise ValueError(f"Unsupported network: {network}")

