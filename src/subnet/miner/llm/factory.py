from src.subnet.miner._config import MinerSettings
from src.subnet.miner.llm.base_llm import BaseLLM
from src.subnet.miner.llm.openai import OpenAILLM
from src.subnet.protocol.llm_engine import LLM_TYPE_OPENAI


class LLMFactory:
    @classmethod
    def create_llm(cls, settings: MinerSettings) -> BaseLLM:
        llm_class = {
            LLM_TYPE_OPENAI: OpenAILLM,
        }.get(settings.LLM_TYPE)

        if llm_class is None:
            raise ValueError(f"Unsupported LLM Type: {settings.LLM_TYPE}")

        return llm_class(settings=settings)