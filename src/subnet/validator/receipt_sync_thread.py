import asyncio
import threading
import traceback
from loguru import logger

from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.receipt_sync import ReceiptSyncWorker


class ReceiptSyncThread(threading.Thread):
    def __init__(self, keypair, settings, client, frequency, terminate_event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keypair = keypair
        self.settings = settings
        self.client = client
        self.frequency = frequency
        self.terminate_event = terminate_event

    async def main(self):

        session_manager = DatabaseSessionManager()
        session_manager.init(self.settings.DATABASE_URL)
        miner_receipt_manager = MinerReceiptManager(session_manager)

        receipt_sync_worker = ReceiptSyncWorker(self.keypair, self.settings.NET_UID, self.client, miner_receipt_manager)
        while not self.terminate_event.is_set():
            next_send_time = asyncio.get_event_loop().time() + (self.frequency * 60)
            try:
                logger.info("Syncing receipts", validator_key=self.keypair.ss58_address)
                await receipt_sync_worker.sync_receipts()
                logger.info("Receipt sync complete", validator_key=self.keypair.ss58_address)
            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Error occurred while receipt sync.", error=e, traceback=tb, validator_key=self.keypair.ss58_address)

            while not self.terminate_event.is_set():
                now = asyncio.get_event_loop().time()
                if now >= next_send_time:
                    break
                await asyncio.sleep(1)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main())
        finally:
            loop.close()