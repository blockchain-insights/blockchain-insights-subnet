from typing import List
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from loguru import logger

from src.subnet.miner._config import MinerSettings
from src.subnet.miner.llm.base_llm import BaseLLM
from src.subnet.miner.llm.prompt_reader import read_local_file
from src.subnet.miner.llm.utils import split_messages_into_chunks
from src.subnet.protocol.llm_engine import LlmMessage, LLM_ERROR_QUERY_BUILD_FAILED, LLM_ERROR_INTERPRETION_FAILED, \
    LLM_ERROR_NOT_APPLICAPLE_QUESTIONS, LLM_ERROR_GENERAL_RESPONSE_FAILED, MODEL_TYPE_FUNDS_FLOW, \
    MODEL_TYPE_BALANCE_TRACKING, LLM_MESSAGE_TYPE_USER


class OpenAILLM(BaseLLM):
    def __init__(self, settings: MinerSettings) -> None:
        self.settings = settings
        self.chat_gpt4o = ChatOpenAI(api_key=settings.LLM_API_KEY, model="gpt-4o", temperature=0)
        self.MAX_TOKENS = 128000

    def determine_model_type(self, llm_messages: List[LlmMessage], network: str) -> str:
        content = self._build_query_from_messages(llm_messages, network, "classification", "classification_prompt.txt")
        if "Funds Flow" in content:
            return MODEL_TYPE_FUNDS_FLOW
        elif "Balance Tracking" in content:
            return MODEL_TYPE_BALANCE_TRACKING
        else:
            logger.error("Received invalid classification from AI response")
            raise Exception("LLM_ERROR_CLASSIFICATION_FAILED")

    def build_query_from_messages_balance_tracker(self, llm_messages: List[LlmMessage], network: str):
        return self._build_query_from_messages(llm_messages, network, "balance_tracking", "query_prompt.txt")

    def build_cypher_query_from_messages(self, llm_messages: List[LlmMessage], network: str):
        return self._build_query_from_messages(llm_messages, network, "funds_flow", "query_prompt.txt")

    def interpret_result_funds_flow(self, llm_messages: list, result: list, network: str):
        return self._interpret_result(result, network, "funds_flow")

    def interpret_result_balance_tracker(self, llm_messages: list, result: list, network: str):
        return self._interpret_result(result, network, "balance_tracking")

    def _build_query_from_messages(self, llm_messages: List[LlmMessage], network: str, subfolder: str, prompt_file_name: str) -> str:
        local_file_path = f"openai/prompts/{network}/{subfolder}/{prompt_file_name}"
        prompt = read_local_file(local_file_path)
        if not prompt:
            raise Exception("Failed to read prompt content")

        messages = [
            SystemMessage(
                content=prompt
            ),
        ]
        for llm_message in llm_messages:
            if llm_message.type == LLM_MESSAGE_TYPE_USER:
                messages.append(HumanMessage(content=llm_message.content))
            else:
                messages.append(AIMessage(content=llm_message.content))
        try:
            ai_message = self.chat_gpt4o.invoke(messages)
            logger.info(f"AI-generated message: {ai_message.content}")
            _ = ai_message.response_metadata['token_usage']
            return ai_message.content
        except Exception as e:
            logger.error(f"LlmQuery build error: {e}")
            raise Exception(LLM_ERROR_QUERY_BUILD_FAILED)

    def _interpret_result(self, result: list, network: str, subfolder: str) -> str:
        local_file_path = f"openai/prompts/{network}/{subfolder}/interpretation_prompt.txt"
        prompt = read_local_file(local_file_path)
        if not prompt:
            raise Exception("Failed to read prompt content")

        if not result:
            logger.warning("The result is empty. Ensure the result data is correctly generated.")
            result_str = "No data available to interpret. Result is empty."
        else:
            try:
                result_str = json.dumps(result, indent=2)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error during result formatting: {e}")
                raise Exception("Error formatting result as JSON") from e
        try:
            full_prompt = prompt.format(result=result_str)
            logger.error(f"Full prompt: {full_prompt}")
        except KeyError as e:
            logger.error(f"KeyError during prompt formatting: {e}")
            logger.error(f"Prompt: {prompt}")
            logger.error(f"Result: {result_str}")
            raise Exception("Error formatting prompt with result") from e

        # Prepare the messages
        messages = [SystemMessage(content=full_prompt)]
        # for llm_message in llm_messages:
        #    if llm_message.type == LLM_MESSAGE_TYPE_USER:
        #        messages.append(HumanMessage(content=llm_message.content))
        #    else:
        #        messages.append(AIMessage(content=llm_message.content))
        try:
            message_chunks = split_messages_into_chunks(messages)
            ai_responses = []
            for chunk in message_chunks:
                ai_message = self.chat_gpt4o.invoke(chunk)
                ai_responses.append(ai_message.content)
            combined_response = "\n".join(ai_responses)
            return combined_response

        except Exception as e:
            logger.error(f"LlmQuery interpret result error: {e}")
            raise Exception(LLM_ERROR_INTERPRETION_FAILED)

    def generate_general_response(self, llm_messages: List[LlmMessage]):
        general_prompt = "Your general prompt here"
        messages = [
            SystemMessage(
                content=general_prompt
            ),
        ]
        for llm_message in llm_messages:
            if llm_message.type == LLM_MESSAGE_TYPE_USER:
                messages.append(HumanMessage(content=llm_message.content))
            else:
                messages.append(AIMessage(content=llm_message.content))
        try:
            ai_message = self.chat_gpt4o.invoke(messages)
            logger.info(f'ai_message using GPT-4  : {ai_message}')
            if ai_message == "not applicable questions":
                raise Exception(LLM_ERROR_NOT_APPLICAPLE_QUESTIONS)
            else:
                return ai_message.content
        except Exception as e:
            logger.error(f"LlmQuery general response error: {e}")
            raise Exception(LLM_ERROR_GENERAL_RESPONSE_FAILED)
