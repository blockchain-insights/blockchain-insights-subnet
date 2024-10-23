from abc import ABC, abstractmethod
from typing import List, Any, Dict, Set

def satoshi_to_btc(satoshi: int) -> float:
    return satoshi / 1e8

class BaseGraphTransformer(ABC):
    @abstractmethod
    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform graph results into a structured format."""
        pass

class BaseTabularTransformer(ABC):
    @abstractmethod
    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform tabular results into a structured format."""
        pass

class BaseChartTransformer(ABC):
    @abstractmethod
    def is_chart_applicable(self, data: List[Dict[str, Any]]) -> bool:
        """Check if data can be transformed into a chart."""
        pass

    @abstractmethod
    def convert_funds_flow_to_chart(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert funds flow data into chart format."""
        pass

    @abstractmethod
    def convert_balance_tracking_to_chart(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert balance tracking data into chart format."""
        pass