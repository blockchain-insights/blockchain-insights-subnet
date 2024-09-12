from loguru import logger as loguru_logger
from substrateinterface import Keypair

logger = loguru_logger


def setup_validator_logger(key_pair: Keypair):
    global logger
    logger = logger.bind(validator_key=key_pair.ss58_address, service='validator')


def setup_validator_api_logger(key_pair: Keypair):
    global logger
    logger = logger.bind(validator_key=key_pair.ss58_address, service='validator-api')