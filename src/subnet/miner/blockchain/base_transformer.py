from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseGraphTransformer(ABC):
    @abstractmethod
    def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform graph results into a structured format."""
        pass


class BaseChartTransformer(ABC):
    @staticmethod
    def is_chart_applicable(data: List[Dict[str, Any]]) -> bool:
        """Check if data can be transformed into a chart."""
        pass

    @staticmethod
    def convert_funds_flow_to_chart(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert funds flow data into chart format."""
        pass

    @staticmethod
    def convert_balance_tracking_to_chart(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert balance tracking data into chart format."""
        pass


class BaseTabularTransformer(ABC):
    @staticmethod
    def transform_result_set(result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform tabular results into a structured format."""
        pass


def satoshi_to_btc(satoshi: int) -> float:
    return satoshi / 1e8


class BaseGraphSummaryTransformer:
    def __init__(self):
        self.total_transactions = 0
        self.incoming_amount = 0
        self.outgoing_amount = 0

    def transform_result(self, result: List[Dict[str, Any]]):
        raise NotImplementedError("Subclasses should implement this method.")

    def process_transaction_entry(self, entry: Dict[str, Any]) -> None:
        raise NotImplementedError("Subclasses should implement this method.")

    def get_btc_value(self, sent_transaction: Dict[str, Any]) -> float:
        value_satoshi = sent_transaction.get('value_satoshi', 0)
        return satoshi_to_btc(value_satoshi)

