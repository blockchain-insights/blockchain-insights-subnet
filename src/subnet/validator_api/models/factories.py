from src.subnet.validator_api.models.bitcoin.graph_result_transformer import BitcoinGraphTransformer
from src.subnet.validator_api.models.chart_result_transformer import ChartTransformer
from src.subnet.validator_api.models.commune.graph_result_transformer import CommuneGraphTransformer
from src.subnet.validator_api.models.tabular_result_transformer import TabularTransformer
from typing import Union

def get_graph_transformer(network: str) -> Union[BitcoinGraphTransformer, CommuneGraphTransformer]:
    if network == "bitcoin":
        return BitcoinGraphTransformer()
    elif network == "commune":
        return CommuneGraphTransformer()
    else:
        raise ValueError(f"Unsupported network: {network}")

def get_tabular_transformer(network: str) ->TabularTransformer:
    return TabularTransformer()

def get_chart_transformer(network: str) -> ChartTransformer:
    return ChartTransformer()

