import signal
from datetime import datetime
from typing import Optional
import uvicorn
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from src.subnet.protocol.llm_engine import LlmQueryRequest
from src.subnet.validator.database.models.api_key import ApiKeyManager
from src.subnet.validator.database.models.challenge_balance_tracking import ChallengeBalanceTrackingManager
from src.subnet.validator.database.models.challenge_funds_flow import ChallengeFundsFlowManager
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager

from src.subnet.validator._config import ValidatorSettings, load_environment
from src.subnet.validator.database.models.validation_prompt import ValidationPromptManager
from src.subnet.validator.database.models.validation_prompt_response import ValidationPromptResponseManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.llm.factory import LLMFactory
from src.subnet.validator.rate_limiter import RateLimiterMiddleware
from src.subnet.validator.validator import Validator
from src.subnet.validator.weights_storage import WeightsStorage


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


api_key_header = APIKeyHeader(name='x-api-key', auto_error = False)


async def api_key_auth(api_key: str = Security(api_key_header)):
    global api_key_manager
    if api_key_manager is None:
        raise HTTPException(status_code=500, detail="API Key Manager not initialized")

    # Use the global api_key_manager created in __main__
    has_access = await api_key_manager.validate_api_key(api_key)
    if not has_access:
        raise HTTPException(status_code=401, detail="Missing or Invalid API key")


class ValidatorApi:
    def __init__(self, validator: Validator):
        self.validator = validator
        self.router = APIRouter()
        self.router.add_api_route("/api/v1/miner/metadata", self.get_miner_metadata, methods=["GET"])
        self.router.add_api_route("/api/v1/miner/query", self.query_miner, methods=["POST"])
        self.router.add_api_route("/api/v1/miner/receipts", self.get_receipts, methods=["GET"])
        self.router.add_api_route("/api/v1/miner/receipts", self.accept_receipt, methods=["POST"])
        self.router.add_api_route("/api/v1/miner/receipts/stats", self.get_receipt_miner_multiplier, methods=["GET"])

    async def get_miner_metadata(self, network: Optional[str] = None, api_key: str = Depends(api_key_auth)):
        results = await self.validator.miner_discovery_manager.get_miners_by_network(network)
        return results

    async def query_miner(self, request: LlmQueryRequest, api_key: str = Depends(api_key_auth)):
        results = await self.validator.query_miner(request)

        """
        
         return {
                "request_id": request_id,
                "timestamp": timestamp,
                "miner_keys": [request.miner_key],
                "prompt_hash": prompt_hash,
                "response": result,
            }
        
        
        response = {
                    "miner_hotkey": str(uuid.UUID(int=0)),
                    "response": [
                        {
                            "type": "text",
                            "result": "cant receive any response due to poor miner network",
                            "interpreted_result":  "cant receive any response due to poor miner network"
                        }
                    ]
                }
        
        """

        return results

    async def get_receipts(self, miner_key: str, page: int = 1, page_size: int = 10, api_key: str = Depends(api_key_auth)):
        results = await self.validator.miner_receipt_manager.get_receipts_by_miner_key(miner_key, page, page_size)
        return results

    async def accept_receipt(self, request_id: str, miner_key: str, api_key: str = Depends(api_key_auth)):
        await self.validator.miner_receipt_manager.accept_miner_receipt(request_id, miner_key)
        return Response(status_code=204)

    async def get_receipt_miner_multiplier(self, miner_key: Optional[str], api_key: str = Depends(api_key_auth)):
        results = await self.validator.miner_receipt_manager.get_receipt_miner_multiplier(miner_key)
        return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m subnet.validator_api <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)

    env = sys.argv[1]
    use_testnet = env == 'testnet'
    load_environment(env)

    settings = ValidatorSettings()
    keypair = classic_load_key(settings.VALIDATOR_KEY)

    def patch_record(record):
        record["extra"]["validator_key"] = keypair.ss58_address
        record["extra"]["service"] = 'validator-api'
        record["extra"]["timestamp"] = datetime.utcnow().isoformat()
        record["extra"]["level"] = record['level'].name

        return True

    logger.remove()
    logger.add(
        "../../logs/validator_api.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        filter=patch_record
    )

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <blue>{message}</blue> | {extra}",
        level="DEBUG",
        filter=patch_record
    )

    c_client = CommuneClient(get_node_url(use_testnet=use_testnet))
    weights_storage = WeightsStorage(settings.WEIGHTS_FILE_NAME)

    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)
    miner_discovery_manager = MinerDiscoveryManager(session_manager)
    miner_receipt_manager = MinerReceiptManager(session_manager)
    validation_prompt_manager = ValidationPromptManager(session_manager)
    validation_prompt_response_manager = ValidationPromptResponseManager(session_manager)
    challenge_funds_flow_manager = ChallengeFundsFlowManager(session_manager)
    challenge_balance_tracking_manager = ChallengeBalanceTrackingManager(session_manager)
    llm = LLMFactory.create_llm(settings)

    global api_key_manager
    api_key_manager = ApiKeyManager(session_manager)

    validator = Validator(
        keypair,
        settings.NET_UID,
        c_client,
        weights_storage,
        miner_discovery_manager,
        validation_prompt_manager,
        validation_prompt_response_manager,
        challenge_funds_flow_manager,
        challenge_balance_tracking_manager,
        miner_receipt_manager,
        llm,
        query_timeout=settings.QUERY_TIMEOUT,
        challenge_timeout=settings.CHALLENGE_TIMEOUT,
        llm_query_timeout=settings.LLM_QUERY_TIMEOUT
    )

    app = FastAPI(
        title="Validator API",
        description="API for managing and querying miner metadata, receipts, and other validator-related operations.",
        version="1.0.0"
    )

    validator_api = ValidatorApi(validator)
    app.include_router(validator_api.router)
    app.add_middleware(RateLimiterMiddleware, redis_url=settings.REDIS_URL, max_requests=settings.API_RATE_LIMIT,
                            window_seconds=60)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def shutdown_handler(signal, frame):
        logger.debug("Shutdown handler started")
        uvicorn_server.should_exit = True
        uvicorn_server.force_exit = True
        logger.debug("Shutdown handler finished")

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    uvicorn_server = uvicorn.Server(config=uvicorn.Config(app, host="0.0.0.0", port=settings.PORT, workers=settings.WORKERS))
    uvicorn_server.run()
