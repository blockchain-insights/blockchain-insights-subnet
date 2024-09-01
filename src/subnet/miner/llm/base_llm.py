from abc import ABC, abstractmethod
from typing import List

from src.subnet.miner._config import MinerSettings
from src.subnet.protocol.llm_engine import LlmMessage


class BaseLLM(ABC):
    @abstractmethod
    def __init__(self, settings: MinerSettings) -> None:
        """
        Initialize LLM
        """

    @abstractmethod
    def build_query_from_messages_balance_tracker(self, llm_messages: List[LlmMessage], network: str):
        """
        Build query synapse from natural language query for balance tracker
        """

    @abstractmethod
    def build_cypher_query_from_messages(self, llm_messages: List[LlmMessage], network: str):
        """
        Build query synapse from natural language query for funds flow
        """

    @abstractmethod
    def interpret_result_funds_flow(self, llm_messages: List[LlmMessage], result: list, network: str):
        """
        Interpret result into natural language based on user's query and structured result dict for funds flow
        """

    @abstractmethod
    def interpret_result_balance_tracker(self, llm_messages: List[LlmMessage], result: list, network: str):
        """
        Interpret result into natural language based on user's query and structured result dict for balance tracker
        """

    @abstractmethod
    def determine_model_type(self, llm_messages: List[LlmMessage], network: str):
        """
        Determine model type based on messages
        """

    @abstractmethod
    def generate_general_response(self, llm_messages: List[LlmMessage]):
        """
        Generate general response based on chat history
        """
