from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings


class BaseLLM(ABC):
    @abstractmethod
    def __init__(self, settings: ValidatorSettings) -> None:
        """
        Initialize LLM
        """

    @abstractmethod
    def build_prompt_from_txid_and_block(self, txid: str, block_height: int, network: str, prompt_template: str):
        """
        Build a validation prompt from a given txid and block
        """



    @abstractmethod
    def determine_model_type(self, prompt: str, network: str):
        """
        Determine model type based on messages
        """

    @abstractmethod
    def validate_query_by_prompt(self, prompt: str, query: str, network: str):
        """
        Validate query by prompt
        """
