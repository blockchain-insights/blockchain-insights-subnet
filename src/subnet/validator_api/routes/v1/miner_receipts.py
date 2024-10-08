from typing import Optional
from fastapi import Depends, APIRouter
from pydantic import BaseModel

from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth

miner_router = APIRouter(prefix="/v1/miner", tags=["miner"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


@miner_router.get("/metadata")
async def get_metadata(network: Optional[str] = None,
                             validator: Validator = Depends(get_validator),
                             api_key: str = Depends(api_key_auth)):
    results = await validator.miner_discovery_manager.get_miners_by_network(network)
    return results


@miner_router.get("/receipts")
async def get_receipts(miner_key: str, page: int = 1, page_size: int = 10,
                       validator: Validator = Depends(get_validator),
                       api_key: str = Depends(api_key_auth)):
    results = await validator.miner_receipt_manager.get_receipts_by_miner_key(miner_key, page, page_size)
    return results


@miner_router.get("/miner/multiplier")
async def get_receipt_multiplier(miner_key: Optional[str] = None, network: Optional[str] = None,
                                       validator: Validator = Depends(get_validator),
                                       api_key: str = Depends(api_key_auth)):
    results = await validator.miner_receipt_manager.get_receipt_miner_multiplier(network, miner_key)
    return results


@miner_router.get("/miner/ranks")
async def get_ranks(network: Optional[str] = None,
                          validator: Validator = Depends(get_validator),
                          api_key: str = Depends(api_key_auth)):
    results = await validator.miner_discovery_manager.get_miners_for_leader_board(network)
    return results