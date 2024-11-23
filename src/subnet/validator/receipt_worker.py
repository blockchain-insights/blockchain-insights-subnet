import json
from aioredis import Redis
import asyncio
import threading
import traceback
from loguru import logger
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager


class ReceiptConsumerThread(threading.Thread):
    def __init__(self, keypair, settings, terminate_event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keypair = keypair
        self.settings = settings
        self.terminate_event = terminate_event

    async def main(self):

        session_manager = DatabaseSessionManager()
        session_manager.init(self.settings.DATABASE_URL)
        miner_receipt_manager = MinerReceiptManager(session_manager)

        redis_client = Redis.from_url(self.settings.REDIS_URL)

        try:
            logger.info("Starting receipt consumer", validator_key=self.keypair.ss58_address)

            while not self.terminate_event.is_set():
                message = await redis_client.brpop('receipts', timeout=5)
                if message:
                    _, receipt_json = message
                    receipt = json.loads(receipt_json)
                    await miner_receipt_manager.store_miner_receipt(**receipt)
                    logger.info("Receipt processed", validator_key=self.keypair.ss58_address)

        except Exception as e:
            tb = traceback.format_exc()
            logger.error("Error occurred while processing receipt.", error=e, traceback=tb, validator_key=self.keypair.ss58_address)
        finally:
            await redis_client.close()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main())
        finally:
            loop.close()