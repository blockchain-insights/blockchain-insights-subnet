from src.subnet.validator.blockchain.common.base_prompt_generator import BasePromptGenerator
from src.subnet.validator.blockchain.bitcoin.prompt_generator import BitcoinPromptGenerator
from src.subnet.validator.blockchain.ethereum.prompt_generator import EthereumPromptGenerator
from src.subnet.protocol.blockchain import NETWORK_BITCOIN, NETWORK_ETHEREUM


class PromptGeneratorFactory:
    @classmethod
    def create_prompt_generator(cls, network: str, settings, llm) -> BasePromptGenerator:
        # Dictionary mapping network types to their corresponding prompt generator classes
        prompt_generator_class = {
            NETWORK_BITCOIN: BitcoinPromptGenerator,
            NETWORK_ETHEREUM: EthereumPromptGenerator,
        }.get(network)

        # Raise an error if the network type is not supported
        if prompt_generator_class is None:
            raise ValueError(f"Unsupported network type: {network}")

        # Instantiate the appropriate prompt generator class with settings, llm, and network
        return prompt_generator_class(settings=settings, llm=llm)
