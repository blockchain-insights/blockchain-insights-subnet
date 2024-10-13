from typing import Optional
from fastapi import Depends, APIRouter, Query
from pydantic import BaseModel
from enum import Enum

from src.subnet.protocol import MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.models.tabular_result_transformer import BitcoinTabularTransformer
from src.subnet.validator_api.services.bitcoin_query_api import BitcoinQueryApi
from src.subnet.validator_api.helpers.reponse_formatter import format_response, ResponseType

# Router for balance tracking
balance_tracking_bitcoin_router = APIRouter(prefix="/v1/balance-tracking", tags=["balance-tracking"])

class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None

@balance_tracking_bitcoin_router.get("/{network}")
async def get_balance_tracking(network: str,
                               addresses: Optional[list[str]] = Query(None),
                               min_amount: Optional[int] = Query(None),
                               max_amount: Optional[int] = Query(None),
                               start_block_height: Optional[int] = Query(None),
                               end_block_height: Optional[int] = Query(None),
                               start_timestamp: Optional[int] = Query(None),
                               end_timestamp: Optional[int] = Query(None),
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
            end_block_height=end_block_height,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp
        )

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinTabularTransformer()  # Assuming a transformer is needed to process the results
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}



@balance_tracking_bitcoin_router.get("/{network}/timestamps")
async def get_timestamps(network: str,
                         start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
                         end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
                         response_type: ResponseType = Query(ResponseType.json),  # Add response type parameter
                         validator: Validator = Depends(get_validator),
                         api_key: str = Depends(api_key_auth)):

    if network == "bitcoin":  # Assuming "bitcoin" is the correct network identifier
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_balance_tracking_timestamp(
            start_date=start_date,
            end_date=end_date
        )

        # Check if data['response'] exists and is not None, otherwise set it to an empty list
        if not data.get('response'):
            data['response'] = []
            data['results'] = []

        # Transform the results if response data exists
        if data['response']:
            transformer = BitcoinTabularTransformer()  # Assuming a transformer is needed to process the results
            data['results'] = transformer.transform_result(data['response'])

        # Handle response based on the response_type
        return format_response(data, response_type)

    return {"results": [], "response": [], "message": "Invalid network."}
