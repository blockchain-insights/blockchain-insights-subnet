from typing import Optional, List
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.subnet.protocol import NETWORK_BITCOIN, NETWORK_COMMUNE
from src.subnet.validator.validator import Validator
from src.subnet.gateway import get_validator, api_key_auth
from src.subnet.gateway.models.factories import get_graph_transformer
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


@funds_flow_router.get("/{network}/get_blocks")
async def get_blocks(
    network: str,
    block_heights: List[int] = Query(..., description="List of block heights (maximum 10)", min_length=1, max_length=10),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_blocks(block_heights)

    if not data.get("response"):
        data["response"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["response"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/get_transaction_by_tx_id")
async def get_transaction_by_tx_id(
    network: str,
    tx_id: str,
    left_hops: int = Query(2, description="Number of hops to the left", ge=0, le=4),
    right_hops: int = Query(2, description="Number of hops to the right", ge=0, le=4),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_blocks_around_transaction(tx_id, left_hops, right_hops)

    if not data.get("response"):
        data["response"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["response"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/get_address_transactions")
async def get_address_transactions(
    network: str,
    address: str = Query(...),
    left_hops: int = Query(2, description="Number of hops to the left", ge=0, le=4),
    right_hops: int = Query(2, description="Number of hops to the right", ge=0, le=4),
    limit: Optional[int] = Query(100),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_address_transactions(
        address=address,
        left_hops=left_hops,
        right_hops=right_hops,
        limit=limit,
    )

    if not data.get("response"):
        data["response"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["response"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/funds-flow")
async def get_funds_flow(
    network: str,
    address: str = Query(...),
    direction: str = Query(..., description="Direction of flow ('left' for incoming, 'right' for outgoing)"),
    intermediate_addresses: Optional[List[str]] = Query(None),
    hops: Optional[int] = Query(None),
    start_block_height: Optional[int] = Query(None),
    end_block_height: Optional[int] = Query(None),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_funds_flow(
        address=address,
        direction=direction,
        intermediate_addresses=intermediate_addresses,
        hops=hops,
        start_block_height=start_block_height,
        end_block_height=end_block_height,
    )

    if not data.get("response"):
        data["response"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["response"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)
