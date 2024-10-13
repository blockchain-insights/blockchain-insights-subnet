from typing import Optional, List
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel

from src.subnet.protocol import MODEL_KIND_FUNDS_FLOW, NETWORK_BITCOIN
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.models.graph_result_transformer import BitcoinGraphTransformer
from src.subnet.validator_api.services.bitcoin_query_api import BitcoinQueryApi
from src.subnet.validator_api.helpers.reponse_formatter import format_response, ResponseType

funds_flow_bitcoin_router = APIRouter(prefix="/v1/funds-flow", tags=["funds-flow"])

class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None

@funds_flow_bitcoin_router.get("/{network}/get_blocks",
                               summary="Get multiple blocks",
                               description="Get multiple blocks"
                               )
async def get_blocks(network: str,
                     block_heights: List[int] = Query(..., description="List of block heights (maximum 10)"),  # Accept list of block heights as query params
                     response_type: ResponseType = Query(ResponseType.json),  # New response type parameter
                     validator: Validator = Depends(get_validator),
                     api_key: str = Depends(api_key_auth)):

    # Ensure the length of the block_heights list does not exceed 10
    if len(block_heights) > 10:
        raise HTTPException(status_code=400, detail="The maximum number of block heights allowed is 10.")

    if network == NETWORK_BITCOIN:
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_blocks(block_heights)

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinGraphTransformer()
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}


@funds_flow_bitcoin_router.get("/{network}/get_transaction_by_tx_id")
async def get_transaction_by_tx_id(network: str,
                                   tx_id: str,
                                   radius: int = Query(0),  # Accept radius as query parameter
                                   response_type: ResponseType = Query(ResponseType.json),  # New response type parameter
                                   validator: Validator = Depends(get_validator),
                                   api_key: str = Depends(api_key_auth)):

    # Ensure that the radius does not exceed 10
    if radius > 10:
        raise ValueError("Radius cannot be greater than 10 blocks")

    if network == NETWORK_BITCOIN:
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_blocks_around_transaction(tx_id, radius)

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinGraphTransformer()
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}


@funds_flow_bitcoin_router.get("/{network}/get_address_transactions")
async def get_address_transactions(network: str,
                                   address: str = Query(...),
                                   start_block_height: Optional[int] = Query(None),
                                   end_block_height: Optional[int] = Query(None),
                                   limit: Optional[int] = Query(100),
                                   response_type: ResponseType = Query(ResponseType.json),  # New response type parameter
                                   validator: Validator = Depends(get_validator),
                                   api_key: str = Depends(api_key_auth)):

    if network == NETWORK_BITCOIN:
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_address_transactions(
            address=address,
            start_block_height=start_block_height,
            end_block_height=end_block_height,
            limit=limit
        )

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinGraphTransformer()
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}


@funds_flow_bitcoin_router.get("/{network}/funds-flow")
async def get_funds_flow(network: str,
                         address: str = Query(...),
                         direction: str = Query(...,
                                                description="Direction of flow ('left' for incoming, 'right' for outgoing)"),
                         intermediate_addresses: Optional[List[str]] = Query(None),
                         hops: Optional[int] = Query(None),
                         start_block_height: Optional[int] = Query(None),
                         end_block_height: Optional[int] = Query(None),
                         response_type: ResponseType = Query(ResponseType.json),  # New response type parameter
                         validator: Validator = Depends(get_validator),
                         api_key: str = Depends(api_key_auth)):

    if network == NETWORK_BITCOIN:
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_funds_flow(
            address=address,
            direction=direction,
            intermediate_addresses=intermediate_addresses,
            hops=hops,
            start_block_height=start_block_height,
            end_block_height=end_block_height
        )

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinGraphTransformer()
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}

