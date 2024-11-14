from typing import Optional, List
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.subnet.protocol import NETWORK_BITCOIN, NETWORK_COMMUNE
from src.subnet.validator.validator import Validator
from src.subnet.gateway import get_validator, api_key_auth
from src.subnet.gateway.services.bitcoin_funds_flow_query_api import BitcoinFundsFlowQueryApi
from src.subnet.gateway.services.commune_funds_flow_query_api import CommuneFundsFlowQueryApi
from src.subnet.gateway.helpers.reponse_formatter import format_response, ResponseType

funds_flow_router = APIRouter(prefix="/v1/funds-flow", tags=["funds-flow"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


def select_query_api(network: str, validator: Validator):
    """Helper function to select the appropriate query API."""
    if network == NETWORK_BITCOIN:
        return BitcoinFundsFlowQueryApi(validator)
    elif network == NETWORK_COMMUNE:
        return CommuneFundsFlowQueryApi(validator)
    raise HTTPException(status_code=400, detail="Invalid network.")


@funds_flow_router.get("/{network}/get_block")
async def get_blocks(
    network: str,
    block_height: int = Query(..., description="Block height"),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_block(block_height)

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/get_transaction_by_tx_id")
async def get_transaction_by_tx_id(
    network: str,
    tx_id: str,
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_blocks_around_transaction(tx_id)

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/get_address_transactions")
async def get_address_transactions(
    network: str,
    address: str = Query(...),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_address_transactions(
        address=address,
    )

    return format_response(data, response_type)