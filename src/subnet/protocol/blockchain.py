# Networks
from pydantic import BaseModel, Field

NETWORK_BITCOIN = "bitcoin"
NETWORK_BITCOIN_ID = 1
NETWORK_ETHEREUM = "ethereum"
NETWORK_ETHEREUM_ID = 2


def get_network_by_id(id):
    return {
        NETWORK_BITCOIN_ID: NETWORK_BITCOIN,
        NETWORK_ETHEREUM_ID: NETWORK_ETHEREUM
    }.get(id)


def get_network_id(network):
    return {
        NETWORK_BITCOIN : NETWORK_BITCOIN_ID,
        NETWORK_ETHEREUM: NETWORK_ETHEREUM_ID
    }.get(network)


def get_networks():
    return [NETWORK_BITCOIN]


class Discovery(BaseModel):
    network: str = Field(NETWORK_BITCOIN, title="The network to discover")
