from loguru import logger as loguru_logger
from substrateinterface import Keypair
import sys

logger = loguru_logger


def setup_validator_logger(key_pair: Keypair):
    global logger

    logger.remove()
    logger.add(
        "../logs/validator.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}",
        level="DEBUG"
    )

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | <level>{message}</level> | {extra}",
        level="DEBUG"
    )

    logger = logger.bind(validator_key=key_pair.ss58_address, service='validator')


def setup_validator_api_logger(key_pair: Keypair):
    global logger

    logger.remove()
    logger.add(
        "../../logs/validator_api.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    logger = logger.bind(validator_key=key_pair.ss58_address, service='validator-api')