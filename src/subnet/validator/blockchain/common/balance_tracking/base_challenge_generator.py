from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager

class BaseChallengeGenerator(ABC):
    def __init__(self, settings: ValidatorSettings):
        self.settings = settings

    @abstractmethod
    async def generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        """
        This method should be implemented by all subclasses to generate challenges specific to a network and model type.
        """
        pass
