from typing import Optional
from fastapi import Depends, APIRouter
from pydantic import BaseModel

from src.subnet.protocol import MODEL_KIND_FUNDS_FLOW, MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth

balance_tracking_bitcoin_router = APIRouter(prefix="/v1/balance-tracking", tags=["balance-tracking"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


@balance_tracking_bitcoin_router.get("/{network}")
async def query(network: str,
                             validator: Validator = Depends(get_validator),
                             api_key: str = Depends(api_key_auth)):

    result = await validator.query_miner(network, MODEL_KIND_BALANCE_TRACKING, "SELECT 1", miner_key=None)
    return result


@balance_tracking_bitcoin_router.get("/{network}/timestamps")
async def get_timestamps(network: str,
                             validator: Validator = Depends(get_validator),
                             api_key: str = Depends(api_key_auth)):

    result = await validator.query_miner(network, MODEL_KIND_BALANCE_TRACKING, "SELECT 1", miner_key=None)
    return result
