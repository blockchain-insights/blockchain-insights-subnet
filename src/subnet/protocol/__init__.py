from pydantic import BaseModel, Field

NETWORK_BITCOIN = "bitcoin"
NETWORK_COMMUNE = "commune"


def get_networks():
    return [NETWORK_COMMUNE, NETWORK_BITCOIN]


class Discovery(BaseModel):
    network: str = Field(NETWORK_BITCOIN, title="The network to discover")
    version: float = Field(1.0, title="The version of the discovery")


# Model types
MODEL_KIND_MONEY_FLOW = "money_flow"
MODEL_KIND_BALANCE_TRACKING = "balance_tracking"
MODEL_KIND_TRANSACTION_STREAM = "transaction_stream"


def get_model_kinds():
    return [MODEL_KIND_MONEY_FLOW, MODEL_KIND_BALANCE_TRACKING]
