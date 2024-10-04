import src.subnet.validator.blockchain.bitcoin.funds_flow.challenge_generator as bitcoin_funds_flow
import src.subnet.validator.blockchain.bitcoin.balance_tracking.challenge_generator as bitcoin_balance_tracking
import src.subnet.validator.blockchain.ethereum.funds_flow.challenge_generator as ethereum_funds_flow
import src.subnet.validator.blockchain.ethereum.balance_tracking.challenge_generator as ethereum_balance_tracking
import src.subnet.validator.blockchain.common.funds_flow.base_challenge_generator as funds_flow
import src.subnet.validator.blockchain.common.balance_tracking.base_challenge_generator as balance_tracking
from src.subnet.protocol import MODEL_KIND_FUNDS_FLOW, MODEL_KIND_BALANCE_TRACKING, NETWORK_BITCOIN, NETWORK_ETHEREUM


class ChallengeGeneratorFactory:
    @classmethod
    def create_challenge_generator(cls, network: str, model: str, settings) -> funds_flow.BaseChallengeGenerator | balance_tracking.BaseChallengeGenerator:
        # Dictionary mapping network and model types to their corresponding challenge generator classes
        challenge_generator_class = {
            (NETWORK_BITCOIN, MODEL_KIND_FUNDS_FLOW): bitcoin_funds_flow.ChallengeGenerator,
            (NETWORK_BITCOIN, MODEL_KIND_BALANCE_TRACKING): bitcoin_balance_tracking.ChallengeGenerator,
            (NETWORK_ETHEREUM, MODEL_KIND_FUNDS_FLOW): ethereum_funds_flow.ChallengeGenerator,
            (NETWORK_ETHEREUM, MODEL_KIND_BALANCE_TRACKING): ethereum_balance_tracking.ChallengeGenerator,
        }.get((network, model))

        # Raise an error if the network/model combination is not supported
        if challenge_generator_class is None:
            raise ValueError(f"Unsupported combination of network: {network} and model: {model}")

        # Instantiate the appropriate challenge generator class with settings and llm
        return challenge_generator_class(settings=settings)
