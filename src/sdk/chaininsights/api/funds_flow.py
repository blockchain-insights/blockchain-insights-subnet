import requests

from src.sdk.chaininsights.config import Config
from src.sdk.chaininsights.models.response_models import GenericResponse


class FundsFlowAPI:
    def __init__(self, config: Config):
        self.config = config

    def get_block(self, network: str, block_height: int, response_type: str = "json") -> GenericResponse:
        """
        Get details of a block on the specified network.
        Supports response types: 'json' and 'graph'.
        """
        url = f"{self.config.base_url}/v1/funds-flow/{network}/get_block"
        headers = {"x-api-key": self.config.api_key}
        params = {"block_height": block_height, "response_type": response_type}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())

    def get_transaction_by_tx_id(self, network: str, tx_id: str, response_type: str = "json") -> GenericResponse:
        """
        Get transaction details by transaction ID.
        Supports response types: 'json' and 'graph'.
        """
        url = f"{self.config.base_url}/v1/funds-flow/{network}/get_transaction_by_tx_id"
        headers = {"x-api-key": self.config.api_key}
        params = {"tx_id": tx_id, "response_type": response_type}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())

    def get_address_transactions(self, network: str, address: str, response_type: str = "json") -> GenericResponse:
        """
        Get transactions for a specific address.
        Supports response types: 'json' and 'graph'.
        """
        url = f"{self.config.base_url}/v1/funds-flow/{network}/get_address_transactions"
        headers = {"x-api-key": self.config.api_key}
        params = {"address": address, "response_type": response_type}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())