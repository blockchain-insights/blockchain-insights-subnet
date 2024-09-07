import asyncio
import signal
import sys
import threading
from abc import ABC, abstractmethod

from loguru import logger
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key

from src.subnet.protocol.blockchain import get_networks
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipts import MinerReceiptManager
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager, run_migrations
from src.subnet.validator.weights_storage import WeightsStorage
from validator._config import ValidatorSettings, load_environment
from validator.validator import Validator
from src.subnet.validator.llm_prompt_utility import main as llm_main


class PromptGeneratorThread(threading.Thread):
    def __init__(self, environment, network, frequency, threshold, terminate_event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.environment = environment
        self.network = network
        self.frequency = frequency
        self.threshold = threshold
        self.terminate_event = terminate_event

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(llm_main(self.network, self.frequency, self.threshold, self.terminate_event))
        finally:
            loop.close()


if __name__ == "__main__":
    logger.remove()
    logger.add(
        "../logs/validator.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    if len(sys.argv) != 2:
        logger.error("Usage: python -m subnet.cli <environment>")
        sys.exit(1)

    environment = sys.argv[1]
    load_environment(environment)

    # Setup configurations
    settings = ValidatorSettings()
    keypair = classic_load_key(settings.VALIDATOR_KEY)
    c_client = CommuneClient(get_node_url(use_testnet=(environment == 'testnet')))
    weights_storage = WeightsStorage(settings.WEIGHTS_FILE_NAME)

    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)

    run_migrations(settings=settings)

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


    def shutdown_handler(signal_num, frame):
        logger.info("Received shutdown signal, stopping...")
        validator.terminate_event.set()
        logger.debug("Shutdown handler finished")

    # Signal handling for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    networks = get_networks()
    prompt_generator_threads=[]

    for network in networks:
        prompt_generator_thread = PromptGeneratorThread(
        environment=environment,
        network=network,
        frequency=settings.PROMPT_FREQUENCY,
        threshold=settings.PROMPT_THRESHOLD,
        terminate_event=validator.terminate_event
        )
        prompt_generator_threads.append(prompt_generator_thread)
        prompt_generator_thread.start()

    try:
        asyncio.run(validator.validation_loop(settings))
    except KeyboardInterrupt:
        logger.info("Validator loop interrupted")

    for thread in prompt_generator_threads:
        thread.join()
        logger.info(f"Prompt generator for {thread.network} stopped successfully.")

    logger.info("Validator and LLM prompt generator stopped successfully.")
