from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings


class BaseLLM(ABC):
    @abstractmethod
    def __init__(self, settings: ValidatorSettings) -> None:
        """
        Initialize LLM
        """

    @abstractmethod
    def build_prompt_from_txid_and_block(self, txid: str, block: str, network: str, prompt_template: str):
        """
        Build a validation prompt from a given txid and block
        """