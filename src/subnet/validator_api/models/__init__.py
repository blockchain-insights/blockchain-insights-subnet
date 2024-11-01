from abc import ABC, abstractmethod
from typing import List, Any, Dict

def satoshi_to_btc(satoshi: int) -> float:
    return satoshi / 1e8

class BaseGraphTransformer(ABC):
    @abstractmethod
    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform graph results into a structured format."""
        pass