import asyncio
import signal
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key

from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipts import MinerReceiptManager
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.weights_storage import WeightsStorage
from validator._config import ValidatorSettings, load_environment
from validator.validator import Validator
from loguru import logger


if __name__ == "__main__":
    import sys

    logger.remove()
    logger.add(
        "../logs/validator.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    if len(sys.argv) != 2:
        logger.error("Usage: python -m subnet.cli <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)

    env = sys.argv[1]
    use_testnet = env == 'testnet'
    load_environment(env)
    settings = ValidatorSettings()
    keypair = classic_load_key(settings.VALIDATOR_KEY)
    c_client = CommuneClient(get_node_url(use_testnet=use_testnet))
    weights_storage = WeightsStorage(settings.WEIGHTS_FILE_NAME)

    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)
    miner_discovery_manager = MinerDiscoveryManager(session_manager)
    miner_receipt_manager = MinerReceiptManager(session_manager)
    validation_prompt_manager = ValidationPromptManager(session_manager)

    validator = Validator(
        keypair,
        settings.NET_UID,
        c_client,
        weights_storage,
        miner_discovery_manager,
        validation_prompt_manager,
        miner_receipt_manager,
        query_timeout=settings.QUERY_TIMEOUT,
        challenge_timeout=settings.CHALLENGE_TIMEOUT,
        llm_query_timeout=settings.LLM_QUERY_TIMEOUT
    )

    def shutdown_handler(signal, frame):
        logger.debug("Shutdown handler started")
        validator.terminate_event.set()
        logger.debug("Shutdown handler finished")

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    asyncio.run(validator.validation_loop(settings))
