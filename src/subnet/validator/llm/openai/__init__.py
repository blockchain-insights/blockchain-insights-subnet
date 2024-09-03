from typing import List, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from loguru import logger

from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.llm.base_llm import BaseLLM
from src.subnet.validator.llm.prompt_reader import read_local_file
from src.subnet.validator.llm.utils import split_messages_into_chunks
from src.subnet.protocol.llm_engine import LLM_ERROR_PROMPT_GENERATION_FAILED


class OpenAILLM(BaseLLM):
    def __init__(self, settings: ValidatorSettings) -> None:
        self.settings = settings
        self.chat_gpt4o = ChatOpenAI(api_key=settings.LLM_API_KEY, model="gpt-4o", temperature=0)
        self.MAX_TOKENS = 128000

    def build_prompt_from_txid_and_block(self, txid: str, block: str, network: str, prompt_template: str) -> str:
        # Read the main prompt template from disk
        local_file_path = f"openai/prompts/{network}/prompt_generation/prompt_generation_prompt.txt"
        prompt = read_local_file(local_file_path)
        if not prompt:
            raise Exception("Failed to read prompt content")

        if not prompt_template:
            logger.warning("The prompt template is empty. Cannot generate a prompt without a valid template.")
            return "Prompt generation failed: Template is required but not provided."

        # Ensure txid and block are strings
        txid_str = str(txid)
        block_str = str(block)

        # Start with the original template
        substituted_template = prompt_template

        # Safely replace placeholders with actual values if they exist in the template
        if '{txid}' in substituted_template:
            substituted_template = substituted_template.replace('{txid}', txid_str)
        if '{block}' in substituted_template:
            substituted_template = substituted_template.replace('{block}', block_str)

        try:
            logger.info(f"Substituted template: {substituted_template}")

            # Substitute the resulting prompt template into the main prompt
            full_prompt = prompt.replace('{prompt_template}', substituted_template)
            logger.info(f"Full prompt after template substitution: {full_prompt}")
        except Exception as e:
            logger.error(f"Error during prompt formatting: {e}")
            logger.error(f"Prompt: {prompt}")
            logger.error(f"Substituted Template: {substituted_template}")
            raise Exception("Error formatting prompt with txid and block") from e

        # Prepare the messages
        messages = [SystemMessage(content=full_prompt)]

        try:
            message_chunks = split_messages_into_chunks(messages)
            ai_responses = []
            for chunk in message_chunks:
                ai_message = self.chat_gpt4o.invoke(chunk)
                ai_responses.append(ai_message.content)
            combined_response = "\n".join(ai_responses)
            return combined_response

        except Exception as e:
            logger.error(f"LlmQuery prompt generation error: {e}")
            raise Exception(LLM_ERROR_PROMPT_GENERATION_FAILED)
