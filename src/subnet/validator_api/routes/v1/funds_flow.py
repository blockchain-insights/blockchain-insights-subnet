from typing import Optional
from fastapi import Depends, APIRouter
from pydantic import BaseModel

from src.subnet.protocol import MODEL_TYPE_FUNDS_FLOW, NETWORK_BITCOIN
from src.subnet.validator.validator import Validator
from src.subnet.validator_api import get_validator, api_key_auth
from src.subnet.validator_api.models import BitcoinGraphTransformer
from src.subnet.validator_api.services.bitcoin_query_api import BitcoinQueryApi

funds_flow_bitcoin_router = APIRouter(prefix="/v1/funds-flow", tags=["funds-flow"])


class MinerMetadataRequest(BaseModel):
    network: Optional[str] = None


@funds_flow_bitcoin_router.get("/{network}/get_block",
                               summary="Get block",
                               description="Get block"
                               )
async def get_block(network: str,
                    block_height: int,
                    validator: Validator = Depends(get_validator),
                    api_key: str = Depends(api_key_auth)):

    if network == NETWORK_BITCOIN:
        query_api = BitcoinQueryApi(validator)
        data = await query_api.get_block(block_height)

        data['results'] = []
        for response in data['response']:
            result = BitcoinGraphTransformer().transform_result(response)
            data['results'].append(result)

        return data

    return []


@funds_flow_bitcoin_router.get("/{network}/get_transaction_by_tx_id")
async def get_transaction_by_tx_id(network: str,
                                   validator: Validator = Depends(get_validator),
                                   api_key: str = Depends(api_key_auth)):
    result = await validator.query_miner(network, MODEL_TYPE_FUNDS_FLOW, "RETURN 1")
    return result


@funds_flow_bitcoin_router.get("/{network}/get_address_transactions")
async def get_address_transactions(network: str,
                                   validator: Validator = Depends(get_validator),
                                   api_key: str = Depends(api_key_auth)):
    result = await validator.query_miner(network, MODEL_TYPE_FUNDS_FLOW, "RETURN 1")
    return result


@funds_flow_bitcoin_router.get("/{network}/funds-flow")
async def query(network: str,
                validator: Validator = Depends(get_validator),
                api_key: str = Depends(api_key_auth)):
    result = await validator.query_miner(network, MODEL_TYPE_FUNDS_FLOW, "RETURN 1")
    return result