import json
from typing import Any
import requests
from communex.client import CommuneClient
from substrateinterface import Keypair
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager


class ReceiptSyncWorker:

    def __init__(
            self,
            keypair: Keypair,
            netuid: int,
            client: CommuneClient,
            miner_receipt_manager: MinerReceiptManager):
        self.keypair = keypair
        self.netuid = netuid
        self.client = client
        self.miner_receipt_manager = miner_receipt_manager
        self.key_to_gateway_urls = {}

    @staticmethod
    def _get_uid_gateway_url_pairs(ss58_to_metadata, uid_to_key, uid_to_incentive, uid_to_dividend):
        for key, metadata in ss58_to_metadata.items():
            if not metadata:
                continue
            try:
                metadata_json = json.loads(metadata)
                gateway_url = metadata_json.get("gateway")
                if gateway_url is None:
                    continue
                uid = next((_uid for _uid, k in uid_to_key.items() if k == key), None)
                if uid and sum(uid_to_incentive[uid]) > 0 and sum(uid_to_dividend[uid]) > 0:
                    yield key, gateway_url
            except (json.JSONDecodeError, KeyError):
                continue

    async def fetch_validators(self):
        request_dict: dict[Any, Any] = {
            "SubspaceModule": [
                ("Keys", [self.netuid]),
                ("Address", [self.netuid]),
                ("Incentive", []),
                ("Dividends", []),
                ("Metadata", [self.netuid]),
            ],
        }

        bulk_query = self.client.query_batch_map(request_dict)
        (
            uid_to_key,
            uid_to_address,
            uid_to_incentive,
            uid_to_dividend,
            ss58_to_metadata,
        ) = (
            bulk_query.get("Keys", {}),
            bulk_query["Address"],
            bulk_query["Incentive"],
            bulk_query["Dividends"],
            bulk_query.get("Metadata", {}),
        )

        key_to_gateway_urls = dict(self._get_uid_gateway_url_pairs(ss58_to_metadata, uid_to_key, uid_to_incentive, uid_to_dividend))
        return key_to_gateway_urls

    async def sync_receipts(self):

        self.key_to_gateway_urls = await self.fetch_validators()

        for key, gateway_url in self.key_to_gateway_urls.items():
            timestamp = await self.miner_receipt_manager.get_last_receipt_timestamp_for_validator_key(key)
            if not timestamp:
                timestamp = "2024-11-01T00:00:00Z"

            validator_signature = self.keypair.sign(timestamp.encode('utf-8')).hex()
            sync_result_json = requests.get(f"{gateway_url}/receipts/sync", params={
                "validator_key": key,
                "validator_signature":  validator_signature,
                "timestamp": timestamp
            })

            total_pages = sync_result_json["total_pages"]
            receipts = json.loads(sync_result_json.json())

            #TODO: we have to verify each miner signature here, if any signature is invalid, we should blacklist given valdiator

            await self.miner_receipt_manager.sync_miner_receipts(receipts)

            for page in range(2, total_pages + 1):
                sync_result_json = requests.get(f"{gateway_url}/receipts/sync", params={
                    "validator_key": key,
                    "validator_signature":  validator_signature,
                    "timestamp": timestamp,
                    "page": page
                })
                receipts = json.loads(sync_result_json.json())
                await self.miner_receipt_manager.sync_miner_receipts(receipts)