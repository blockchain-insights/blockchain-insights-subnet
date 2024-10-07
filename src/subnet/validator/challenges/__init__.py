import threading
from abc import ABC, abstractmethod
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager


class ChallengeGenerator(ABC):
    def __init__(self, settings: ValidatorSettings, terminate_event: threading.Event):
        self.settings = settings
        self.terminate_event = terminate_event

    @abstractmethod
    async def funds_flow_generate_and_store(self, challenge_manager: ChallengeFundsFlowManager, threshold: int):
        """
        This method should be implemented by all subclasses to generate challenges specific to a network and model type.
        """
        pass

    @abstractmethod
    async def balance_tracking_generate_and_store(self, challenge_manager: ChallengeBalanceTrackingManager, threshold: int):
        """
        This method should be implemented by all subclasses to generate challenges specific to a network and model type.
        """
        pass




