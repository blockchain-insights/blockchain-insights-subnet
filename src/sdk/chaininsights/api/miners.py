import requests

from src.sdk.chaininsights.config import Config
from src.sdk.chaininsights.models.response_models import GenericResponse


class MinersAPI:
    def __init__(self, config: Config):
        self.config = config

    def get_metadata(self, network: str = None) -> GenericResponse:
        url = f"{self.config.base_url}/v1/miner/metadata"
        headers = {"x-api-key": self.config.api_key}
        params = {"network": network}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())

    def get_receipts(self, miner_key: str = None, validator_key: str = None, page: int = 1, page_size: int = 10) -> GenericResponse:
        url = f"{self.config.base_url}/v1/miner/receipts"
        headers = {"x-api-key": self.config.api_key}
        params = {"miner_key": miner_key, "validator_key": validator_key, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())

    def sync_receipts(self, validator_key: str, validator_signature: str, timestamp: str, page: int = 1, page_size: int = 1000) -> GenericResponse:
        url = f"{self.config.base_url}/v1/miner/receipts/sync"
        headers = {"x-api-key": self.config.api_key}
        params = {"validator_key": validator_key, "validator_signature": validator_signature, "timestamp": timestamp, "page": page, "page_size": page_size}
        response = requests.get(url, headers=headers, params=params)
        return GenericResponse(**response.json())
