import json
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import aiohttp
from loguru import logger
from substrateinterface import Keypair
from communex.client import CommuneClient
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager


class ReceiptSyncWorker:
    def __init__(
            self,
            keypair: Keypair,
            netuid: int,
            client: CommuneClient,
            miner_receipt_manager: MinerReceiptManager
    ):
        self.keypair = keypair
        self.netuid = netuid
        self.client = client
        self.miner_receipt_manager = miner_receipt_manager
        self.key_to_gateway_urls: Dict[str, str] = {}
        self.DEFAULT_TIMESTAMP = "2024-11-01T00:00:00Z"
        self.REQUEST_TIMEOUT = 30  # seconds
        self.MAX_CONCURRENT_REQUESTS = 10  # Limit concurrent requests
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    async def session(self) -> aiohttp.ClientSession:
        """Lazy session initialization for thread safety."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def cleanup(self):
        """Cleanup resources - should be called when done with the worker."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @staticmethod
    def _get_uid_gateway_url_pairs(
            ss58_to_metadata: Dict[str, str],
            uid_to_key: Dict[int, str],
            uid_to_incentive: Dict[int, List[float]],
            uid_to_dividend: Dict[int, List[float]]
    ) -> List[Tuple[str, str]]:
        """Extract valid gateway URL pairs from validator metadata."""
        for key, metadata in ss58_to_metadata.items():
            if not metadata:
                continue
            try:
                metadata_json = json.loads(metadata)
                gateway_url = metadata_json.get("gateway")
                if gateway_url is None:
                    continue
                uid = next((_uid for _uid, k in uid_to_key.items() if k == key), None)
                if uid_to_incentive.get(uid) and uid_to_dividend.get(uid):
                    if uid and sum(uid_to_incentive[uid]) > 0 and sum(uid_to_dividend[uid]) > 0:
                        yield key, gateway_url
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error parsing metadata for key {key}: {e}")
                continue

    async def fetch_validators(self) -> Dict[str, str]:
        """Fetch validator information from the network."""
        request_dict: Dict[str, List[Tuple[str, List[Any]]]] = {
            "SubspaceModule": [
                ("Keys", [self.netuid]),
                ("Address", [self.netuid]),
                ("Incentive", []),
                ("Dividends", []),
                ("Metadata", [self.netuid]),
            ],
        }

        bulk_query = self.client.query_batch_map(request_dict)
        uid_to_key = bulk_query.get("Keys", {})
        uid_to_address = bulk_query["Address"]
        uid_to_incentive = bulk_query["Incentive"]
        uid_to_dividend = bulk_query["Dividends"]
        ss58_to_metadata = bulk_query.get("Metadata", {})

        return dict(self._get_uid_gateway_url_pairs(
            ss58_to_metadata, uid_to_key, uid_to_incentive, uid_to_dividend
        ))

    def validate_receipt_signatures(self, receipts: List[dict]) -> bool:
        """Validate signatures for a batch of receipts."""
        for receipt in receipts:
            missing_fields = []
            for field in ["result_hash_signature", "result_hash", "miner_key"]:
                if not receipt.get(field):
                    logger.warning(f"{field} is missing in receipt: {receipt}")
                    missing_fields.append(field)

            if missing_fields:
                continue

            try:
                keypair = Keypair(ss58_address=receipt["miner_key"])
                if not keypair.verify(
                        receipt["result_hash"].encode('utf-8'),
                        bytes.fromhex(receipt["result_hash_signature"])
                ):
                    logger.warning(f"Invalid signature in receipt: {receipt}")
                    return False
            except Exception as e:
                logger.error(f"Error validating receipt signature: {e}")
                return False
        return True

    async def process_page_receipts(self, response_data: dict, gateway_url: str) -> bool:
        """Process a page of receipts including validation and storage."""
        try:
            receipts = response_data['data']
            if receipts is None or receipts == []:
                logger.info(f"No receipts found in response from {gateway_url}")
                return False
            if not self.validate_receipt_signatures(receipts):
                return False
            await self.miner_receipt_manager.sync_miner_receipts(receipts)
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error processing receipts from {gateway_url}: {e}")
            return False

    async def fetch_page(
            self,
            gateway_url: str,
            timestamp: str,
            page: int = 1
    ) -> Optional[dict]:
        """Fetch a single page of receipts with error handling."""

        # Generate signature including page number for better security
        validator_signature = self.keypair.sign(
            timestamp.encode('utf-8')
        ).hex()

        params = {
            "validator_key": self.keypair.ss58_address,
            "validator_signature": validator_signature,
            "timestamp": timestamp
        }
        if page > 1:
            params["page"] = page

        try:
            session = await self.session
            async with session.get(
                    f"{gateway_url}/v1/miner/receipts/sync",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            ) as response:
                if response.status != 200:
                    logger.warning(
                        f"Failed to fetch receipts from {gateway_url}, "
                        f"status: {response.status}"
                    )
                    return None

                return await response.json()

        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching from {gateway_url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from {gateway_url}: {e}")
            return None

    async def sync_single_gateway(self, validator_key: str, gateway_url: str):
        """Synchronize receipts from a single gateway."""
        timestamp_result = await self.miner_receipt_manager.get_last_receipt_timestamp_for_validator_key(validator_key)
        timestamp = timestamp_result['timestamp'] or self.DEFAULT_TIMESTAMP
        first_page_result = await self.fetch_page(gateway_url, timestamp)

        if not first_page_result:
            return

        if not await self.process_page_receipts(first_page_result, gateway_url):
            return

        # Process remaining pages concurrently with rate limiting
        total_pages = first_page_result.get("total_pages", 1)
        if total_pages > 1:
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

            async def fetch_and_process_page(page: int):
                async with semaphore:
                    result = await self.fetch_page(
                        gateway_url, timestamp, page
                    )
                    if result:
                        await self.process_page_receipts(result, gateway_url)

            tasks = [
                fetch_and_process_page(page)
                for page in range(2, total_pages + 1)
            ]
            await asyncio.gather(*tasks)

    async def sync_key_to_gateway_urls(self):
        try:
            self.key_to_gateway_urls = await self.fetch_validators()
        except Exception as e:
            logger.error(f"Error fetching validators", error=e, validator_key=self.keypair.ss58_address)

    async def sync_receipts(self):
        """Main entry point for syncing receipts from all gateways."""
        try:
            self.key_to_gateway_urls = await self.fetch_validators()

            # Process gateways concurrently
            tasks = [
                self.sync_single_gateway(validator_key, gateway_url)
                for validator_key, gateway_url in self.key_to_gateway_urls.items()
            ]
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Error during receipt synchronization: {e}")
            raise
        finally:
            # Cleanup session at the end of each sync
            await self.cleanup()