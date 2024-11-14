from src.subnet.gateway.models.commune.graph_result_transformer import CommuneGraphTransformer
from typing import Union

def get_graph_transformer(network: str) -> Union[CommuneGraphTransformer]:
    if network == "commune":
        return CommuneGraphTransformer()
    else:
        raise ValueError(f"Unsupported network: {network}")


