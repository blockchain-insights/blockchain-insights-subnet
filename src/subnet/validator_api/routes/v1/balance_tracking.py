import re
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.services.balance_tracking_query_api import BalanceTrackingQueryAPI
from src.subnet.validator_api.helpers.reponse_formatter import format_response, ResponseType

# Router for balance tracking
balance_tracking_router = APIRouter(prefix="/v1/balance-tracking", tags=["balance-tracking"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


def validate_date_format(date_str: str) -> datetime:
    """Validate and parse UTC date string in YYYY-MM-DD format"""
    pattern = r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$'
    if not re.match(pattern, date_str):
        raise HTTPException(
            status_code=400,
            detail="Date must be in YYYY-MM-DD format (UTC)"
        )

    try:
        # Parse date and set it to UTC timezone
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date value"
        )


def get_date_range(
        start_date: Optional[str],
        end_date: Optional[str]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Convert and validate UTC date range"""
    start_dt = None
    end_dt = None

    if start_date:
        start_dt = validate_date_format(start_date)
        start_dt = start_dt.replace(hour=0, minute=0, second=0)

    if end_date:
        end_dt = validate_date_format(end_date)
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be later than end_date"
        )

    return start_dt, end_dt


@balance_tracking_router.get("/{network}")
async def get_balance_tracking(
        network: str,
        addresses: Optional[List[str]] = Query(None, description="List of addresses to track"),
        min_amount: Optional[int] = Query(None, description="Minimum amount filter", ge=0),
        max_amount: Optional[int] = Query(None, description="Maximum amount filter", ge=0),
        start_block_height: Optional[int] = Query(
            None,
            description="Starting block height",
            ge=0,
        ),
        end_block_height: Optional[int] = Query(
            None,
            description="Ending block height",
            ge=0,
        ),
        start_date: Optional[str] = Query(
            None,
            description="Start date in YYYY-MM-DD format (UTC)",
        ),
        end_date: Optional[str] = Query(
            None,
            description="End date in YYYY-MM-DD format (UTC)",
        ),
        response_type: ResponseType = Query(
            ResponseType.json,
            description="Response format type"
        ),
        validator: Validator = Depends(get_validator),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(25, ge=1, le=100, description="Items per page"),
        api_key: str = Depends(api_key_auth),
):
    # Validate block heights
    if start_block_height is not None and end_block_height is not None:
        if start_block_height > end_block_height:
            raise HTTPException(
                status_code=400,
                detail="start_block_height cannot be greater than end_block_height"
            )

    # Convert dates to timestamps for the query API
    start_timestamp = None
    end_timestamp = None
    if start_date or end_date:
        start_dt, end_dt = get_date_range(start_date, end_date)
        if start_dt:
            start_timestamp = int(start_dt.timestamp())
        if end_dt:
            end_timestamp = int(end_dt.timestamp())

    query_api = BalanceTrackingQueryAPI(validator)
    data = await query_api.get_balance_tracking(
        network=network,
        addresses=addresses,
        min_amount=min_amount,
        max_amount=max_amount,
        start_block_height=start_block_height,
        end_block_height=end_block_height,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        page=page,
        page_size=page_size,
    )

    return format_response(data, response_type)


@balance_tracking_router.get("/{network}/timestamps")
async def get_timestamps(
        network: str,
        start_date: Optional[str] = Query(
            None,
            description="Start date in YYYY-MM-DD format (UTC)",
        ),
        end_date: Optional[str] = Query(
            None,
            description="End date in YYYY-MM-DD format (UTC)",
        ),
        response_type: ResponseType = Query(
            ResponseType.json,
            description="Response format type"
        ),
        validator: Validator = Depends(get_validator),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(25, ge=1, le=100, description="Items per page"),
        api_key: str = Depends(api_key_auth),
):
    # Validate date formats if provided
    if start_date and not validate_date_format(start_date):
        raise HTTPException(
            status_code=400,
            detail="start_date must be in YYYY-MM-DD format (UTC)"
        )

    if end_date and not validate_date_format(end_date):
        raise HTTPException(
            status_code=400,
            detail="end_date must be in YYYY-MM-DD format (UTC)"
        )

    # Validate date range if both dates are provided
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if start > end:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be later than end_date"
            )

    query_api = BalanceTrackingQueryAPI(validator)
    data = await query_api.get_balance_tracking_timestamp(
        network=network,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return format_response(data, response_type)