from typing import Optional
from fastapi import Depends, APIRouter, Query
from pydantic import BaseModel
from enum import Enum

from src.subnet.protocol import MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.models.tabular_result_transformer import BitcoinTabularTransformer
from src.subnet.validator_api.services.bitcoin_query_api import BitcoinQueryApi
from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime


# Define the ResponseType Enum
class ResponseType(str, Enum):
    json = "json"
    graph = "graph"


# Router for balance tracking
balance_tracking_bitcoin_router = APIRouter(prefix="/v1/balance-tracking", tags=["balance-tracking"])


# Function to format the response based on response type
def format_response(data: dict, response_type: ResponseType):
    """Helper function to format response based on response_type."""

    def serialize_datetime(obj):
        """Helper function to convert datetime objects to string."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    # Recursively walk through the data and convert datetime to string
    def process_data(data):
        if isinstance(data, dict):
            return {key: process_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [process_data(item) for item in data]
        else:
            return serialize_datetime(data)

    processed_data = process_data(data)  # Ensure that datetime objects are handled for JSON or graph response

    if response_type == ResponseType.graph:
        # For graph format, use the processed data and a custom media type
        return JSONResponse(content=processed_data, media_type="application/vnd.graph+json")

    # Default to JSON response
    return JSONResponse(content=processed_data)



class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None

@balance_tracking_bitcoin_router.get("/{network}")
async def get_balance_tracking(network: str,
                               addresses: Optional[list[str]] = Query(None),
                               min_amount: Optional[int] = Query(None),
                               max_amount: Optional[int] = Query(None),
                               start_block_height: Optional[int] = Query(None),
                               end_block_height: Optional[int] = Query(None),
                               response_type: ResponseType = Query(ResponseType.json),  # New response type parameter
                               validator: Validator = Depends(get_validator),
                               api_key: str = Depends(api_key_auth)):
    if network == "bitcoin":  # Assuming "bitcoin" is the network type for balance tracking
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_balance_tracking(
            addresses=addresses,
            min_amount=min_amount,
            max_amount=max_amount,
            start_block_height=start_block_height,
            end_block_height=end_block_height
        )

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinTabularTransformer()
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}


@balance_tracking_bitcoin_router.get("/{network}/timestamps")
async def get_timestamps(network: str,
                         validator: Validator = Depends(get_validator),
                         api_key: str = Depends(api_key_auth)):
    result = await validator.query_miner(network, MODEL_KIND_BALANCE_TRACKING, "SELECT block_timestamp FROM blocks",
                                         miner_key=None)
    return result
