from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings


class BaseLLM(ABC):
    @abstractmethod
    def __init__(self, settings: ValidatorSettings) -> None:
        """
        Initialize LLM
        """

    @abstractmethod
    def build_prompt_from_wallet_address(self, wallet_address: list, network: str):
        """
        Build a validation prompt from a given wallet address
        """