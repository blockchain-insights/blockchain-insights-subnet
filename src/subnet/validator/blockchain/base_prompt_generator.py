from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings

class BasePromptGenerator(ABC):
    def __init__(self, settings: ValidatorSettings):
        self.settings = settings

    @abstractmethod
    def generate_prompt(self, tx_id: str, block: str) -> str:
        """
        This method should be implemented by all subclasses to generate prompts specific to a network.
        """
        pass

    @abstractmethod
    def get_random_txid_and_block(self):
        """
        Method to get a random transaction ID and block from the network.
        """
        pass
