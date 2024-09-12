from loguru import logger as loguru_logger
from substrateinterface import Keypair
import sys

logger = loguru_logger


def setup_miner_logger(key_pair: Keypair):
    global logger

    logger.remove()
    logger.add(
        "../logs/miner.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    logger = logger.bind(miner_key=key_pair.ss58_address, service='miner')
