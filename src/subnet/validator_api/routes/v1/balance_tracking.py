from typing import Optional, List
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel

from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.models.factories import get_tabular_transformer
from src.subnet.validator_api.services.bitcoin_query_api import BitcoinQueryApi
from src.subnet.validator_api.services.commune_query_api import CommuneQueryApi
from src.subnet.validator_api.helpers.reponse_formatter import format_response, ResponseType

# Router for balance tracking
balance_tracking_router = APIRouter(prefix="/v1/balance-tracking", tags=["balance-tracking"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


def select_query_api(network: str, validator: Validator):
    """Helper function to select the appropriate query API."""
    if network == "bitcoin":
        return BitcoinQueryApi(validator)
    elif network == "commune":
        return CommuneQueryApi(validator)
    raise HTTPException(status_code=400, detail="Invalid network.")


@balance_tracking_router.get("/{network}")
async def get_balance_tracking(
    network: str,
    addresses: Optional[List[str]] = Query(None),
    min_amount: Optional[int] = Query(None),
    max_amount: Optional[int] = Query(None),
    start_block_height: Optional[int] = Query(None),
    end_block_height: Optional[int] = Query(None),
    start_timestamp: Optional[int] = Query(None),
    end_timestamp: Optional[int] = Query(None),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_balance_tracking(
        addresses=addresses,
        min_amount=min_amount,
        max_amount=max_amount,
        start_block_height=start_block_height,
        end_block_height=end_block_height,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )

    if not data.get("response"):
        data["response"] = []
        data["results"] = []

    if data["response"]:
        transformer = get_tabular_transformer(network)  # Use the factory here
        data["results"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)


@balance_tracking_router.get("/{network}/timestamps")
async def get_timestamps(
    network: str,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    response_type: ResponseType = Query(ResponseType.json),
    validator: Validator = Depends(get_validator),
    api_key: str = Depends(api_key_auth),
):
    query_api = select_query_api(network, validator)
    data = await query_api.get_balance_tracking_timestamp(
        start_date=start_date, end_date=end_date
    )

    if not data.get("response"):
        data["response"] = []
        data["results"] = []

    if data["response"]:
        transformer = get_tabular_transformer(network)  # Use the factory here
        data["results"] = transformer.transform_result(data["response"])

    return format_response(data, response_type)
