import re
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import Depends, APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.services.balance_tracking_query_api import BalanceTrackingQueryAPI


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
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date value"
        )


@balance_tracking_router.get("/{network}/deltas")
async def get_balance_deltas(
        network: str,
        addresses: List[str] = Query(None, description="List of addresses to track"),
        validator: Validator = Depends(get_validator),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
        api_key: str = Depends(api_key_auth),
):

    if not addresses:
        raise HTTPException(
            status_code=400,
            detail="At least one address must be provided"
        )

    if len(addresses) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 1000 addresses can be provided"
        )

    query_api = BalanceTrackingQueryAPI(validator)
    data = await query_api.get_balance_deltas(
        network=network,
        addresses=addresses,
        page=page,
        page_size=page_size,
    )

    return data


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
        validator: Validator = Depends(get_validator),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
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

    return data