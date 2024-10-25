from typing import Optional, List
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel

from src.subnet.protocol import NETWORK_BITCOIN, NETWORK_COMMUNE
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.models.factories import get_graph_transformer  # Import the factory
from src.subnet.validator_api.services.bitcoin_query_api import BitcoinQueryApi
from src.subnet.validator_api.services.commune_query_api import CommuneQueryApi
from src.subnet.validator_api.helpers.reponse_formatter import format_response, ResponseType

funds_flow_router = APIRouter(prefix="/v1/funds-flow", tags=["funds-flow"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


def select_query_api(network: str, validator: Validator):
    """Helper function to select the appropriate query API."""
    if network == NETWORK_BITCOIN:
        return BitcoinQueryApi(validator)
    elif network == NETWORK_COMMUNE:
        return CommuneQueryApi(validator)
    raise HTTPException(status_code=400, detail="Invalid network.")


@funds_flow_router.get("/{network}/get_blocks")
async def get_blocks(
    network: str,
    block_heights: List[int] = Query(..., description="List of block heights (maximum 10)"),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    if len(block_heights) > 10:
        raise HTTPException(status_code=400, detail="The maximum number of block heights allowed is 10.")

    query_api = select_query_api(network, validator)
    data = await query_api.get_blocks(block_heights)

    if not data.get("response"):
        data["response"] = []
        data["results"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["results"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/get_transaction_by_tx_id")
async def get_transaction_by_tx_id(
    network: str,
    tx_id: str,
    left_hops: int = Query(0),
    right_hops: int = Query(0),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    if left_hops > 4 or right_hops > 4:
        raise HTTPException(status_code=400, detail="Hops cannot exceed 4 in either direction")

    query_api = select_query_api(network, validator)
    data = await query_api.get_blocks_around_transaction(tx_id, left_hops, right_hops)

    if not data.get("response"):
        data["response"] = []
        data["results"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["results"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)


@funds_flow_router.get("/{network}/get_address_transactions")
async def get_address_transactions(
    network: str,
    address: str = Query(...),
    start_block_height: Optional[int] = Query(None),
    end_block_height: Optional[int] = Query(None),
    limit: Optional[int] = Query(100),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_address_transactions(
        address=address,
        start_block_height=start_block_height,
        end_block_height=end_block_height,
        limit=limit,
    )

    if not data.get("response"):
        data["response"] = []
        data["results"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["results"] = transformer.transform_result(data["response"])

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
        data["results"] = []

    if data["response"]:
        transformer = get_graph_transformer(network)  # Use the factory here
        data["results"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)
