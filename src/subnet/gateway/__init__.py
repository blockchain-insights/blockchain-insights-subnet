from datetime import datetime

from aioredis import Redis
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key
import sys
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from loguru import logger
from substrateinterface import Keypair
from src.subnet.validator.database.models.api_key import ApiKeyManager
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.database.models.challenge_money_flow import ChallengeMoneyFlowManager
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager
from src.subnet.validator._config import load_environment, SettingsManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.gateway.rate_limiter import RateLimiterMiddleware
from src.subnet.validator.receipt_sync import ReceiptSyncWorker
from src.subnet.validator.receipt_sync_fetch_thread import ReceiptSyncFetchThread
from src.subnet.validator.validator import Validator
from src.subnet.validator.weights_storage import WeightsStorage

if len(sys.argv) != 2:
    env = 'mainnet'
else:
    env = sys.argv[1]
use_testnet = env == 'testnet'
load_environment(env)

settings_manager = SettingsManager.get_instance()
settings = settings_manager.get_settings()

if settings.VALIDATOR_KEY is None:
    keypair = Keypair.create_from_private_key(settings.VALIDATOR_PRIVATE_KEY, ss58_format=42)
elif settings.VALIDATOR_PRIVATE_KEY is None:
    keypair = classic_load_key(settings.VALIDATOR_KEY)
else:
    logger.error("Both VALIDATOR_KEY and VALIDATOR_PRIVATE_KEY are set, only one should be set")
    sys.exit(1)


def patch_record(record):
    record["extra"]["validator_key"] = keypair.ss58_address
    record["extra"]["service"] = 'gateway'
    record["extra"]["timestamp"] = datetime.utcnow().isoformat()
    record["extra"]["level"] = record['level'].name

    return True


c_client = CommuneClient(get_node_url(use_testnet=use_testnet))
weights_storage = WeightsStorage(settings.WEIGHTS_FILE_NAME)

session_manager = DatabaseSessionManager()
session_manager.init(settings.DATABASE_URL)
miner_discovery_manager = MinerDiscoveryManager(session_manager)
miner_receipt_manager = MinerReceiptManager(session_manager)
challenge_money_flow_manager = ChallengeMoneyFlowManager(session_manager)
challenge_balance_tracking_manager = ChallengeBalanceTrackingManager(session_manager)
receipt_sync_worker = ReceiptSyncWorker(keypair, settings.NET_UID, c_client, miner_receipt_manager)
redis_client = Redis.from_url(settings.REDIS_URL)

global api_key_manager, validator, receipt_sync_fetch_thread

api_key_manager = ApiKeyManager(session_manager)

validator = Validator(
    keypair,
    settings.NET_UID,
    c_client,
    weights_storage,
    miner_discovery_manager,
    challenge_money_flow_manager,
    challenge_balance_tracking_manager,
    miner_receipt_manager,
    redis_client=redis_client,
    query_timeout=settings.QUERY_TIMEOUT,
    challenge_timeout=settings.CHALLENGE_TIMEOUT,
)

receipt_sync_fetch_thread = ReceiptSyncFetchThread(
    keypair=keypair,
    settings=settings,
    receipt_sync_worker=receipt_sync_worker,
    frequency=settings.RECEIPT_SYNC_FREQUENCY,
    terminate_event=validator.terminate_event
)


def get_validator():
    return validator

def get_receipt_sync_worker():
    return receipt_sync_worker

api_key_header = APIKeyHeader(name='x-api-key', auto_error=False)


async def api_key_auth(api_key: str = Security(api_key_header)):
    global api_key_manager
    if api_key_manager is None:
        raise HTTPException(status_code=500, detail="Gateway API Key Manager not initialized")
    has_access = await api_key_manager.validate_api_key(api_key)
    if not has_access:
        raise HTTPException(status_code=401, detail="Missing or Invalid Gateway API key")



