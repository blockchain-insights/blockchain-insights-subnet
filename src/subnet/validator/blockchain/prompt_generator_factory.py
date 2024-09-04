from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.prompt_generators.base_prompt_generator import BasePromptGenerator
from src.subnet.validator.prompt_generators.bitcoin_prompt_generator import BitcoinPromptGenerator
from src.subnet.validator.prompt_generators.ethereum_prompt_generator import EthereumPromptGenerator


NETWORK_TYPE_BITCOIN = "bitcoin"
NETWORK_TYPE_ETHEREUM = "ethereum"


class PromptGeneratorFactory:
    @classmethod
    def create_prompt_generator(cls, settings: ValidatorSettings) -> BasePromptGenerator:
        prompt_generator_class = {
            NETWORK_TYPE_BITCOIN: BitcoinPromptGenerator,
            NETWORK_TYPE_ETHEREUM: EthereumPromptGenerator,
        }.get(settings.NETWORK_TYPE)

        if prompt_generator_class is None:
            raise ValueError(f"Unsupported network type: {settings.NETWORK_TYPE}")

        return prompt_generator_class(settings=settings)

