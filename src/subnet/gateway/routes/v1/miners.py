from typing import Optional
from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from substrateinterface import Keypair

from src.subnet.validator.validator import Validator
from src.subnet.gateway import get_validator, api_key_auth

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


@miner_router.get("/receipts/sync")
async def sync_receipts(validator_key: str, validator_signature: str, timestamp: str, page: int = 1, page_size: int = 1000,
                       validator: Validator = Depends(get_validator)):

    keypair = Keypair(ss58_address=validator_key)
    message = timestamp.encode('utf-8')
    if not keypair.verify(message, validator_signature):
        raise HTTPException(status_code=400, detail="Invalid validator signature")

    results = await validator.miner_receipt_manager.get_receipts_by_to_sync(validator_key, timestamp, page, page_size)
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

@miner_router.get("/miner/networks")
async def get_miners_per_network(
                          validator: Validator = Depends(get_validator),
                          api_key: str = Depends(api_key_auth)):
    results = await validator.miner_discovery_manager.get_miners_per_network()
    return results
