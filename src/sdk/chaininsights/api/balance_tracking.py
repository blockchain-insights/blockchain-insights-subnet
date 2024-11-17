import requests

from src.sdk.chaininsights.config import Config
from src.sdk.chaininsights.models.response_models import GenericResponse


class BalanceTrackingAPI:
    def __init__(self, config: Config):
        self.config = config

    def get_balance_deltas(self, network: str, addresses: list[str] = [], page: int = 1, page_size: int = 100) -> GenericResponse:
        url = f"{self.config.base_url}/v1/balance-tracking/{network}/deltas"
        headers = {"x-api-key": self.config.api_key}
        params = {"addresses": addresses, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())

    def get_balances(self, network: str, addresses: list[str] = [], page: int = 1, page_size: int = 100) -> GenericResponse:
        url = f"{self.config.base_url}/v1/balance-tracking/{network}"
        headers = {"x-api-key": self.config.api_key}
        params = {"addresses": addresses, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())

    def get_timestamps(self, network: str, start_date: str = None, end_date: str = None, page: int = 1, page_size: int = 100) -> GenericResponse:
        url = f"{self.config.base_url}/v1/balance-tracking/{network}/timestamps"
        headers = {"x-api-key": self.config.api_key}
        params = {"start_date": start_date, "end_date": end_date, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())
