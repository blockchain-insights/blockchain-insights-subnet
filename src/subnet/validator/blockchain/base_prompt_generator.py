from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.llm.base_llm import BaseLLM

class BasePromptGenerator(ABC):
    def __init__(self, settings: ValidatorSettings):
        self.settings = settings

    @abstractmethod
    async def generate_and_store(self, validation_prompt_manager: ValidationPromptManager, threshold: int):
        """
        This method should be implemented by all subclasses to generate prompts specific to a network.
        """
        pass