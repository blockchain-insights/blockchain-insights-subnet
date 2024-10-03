from typing import Optional, Dict
from pydantic import BaseModel, Field

NETWORK_BITCOIN = "bitcoin"
NETWORK_BITCOIN_ID = 1
NETWORK_ETHEREUM = "ethereum"
NETWORK_ETHEREUM_ID = 2


def get_network_by_id(id):
    return {
        NETWORK_BITCOIN_ID: NETWORK_BITCOIN,
        NETWORK_ETHEREUM_ID: NETWORK_ETHEREUM
    }.get(id)


def get_network_id(network):
    return {
        NETWORK_BITCOIN: NETWORK_BITCOIN_ID,
        NETWORK_ETHEREUM: NETWORK_ETHEREUM_ID
    }.get(network)


def get_networks():
    return [NETWORK_BITCOIN]


class Discovery(BaseModel):
    network: str = Field(NETWORK_BITCOIN, title="The network to discover")


# Model types
MODEL_TYPE_FUNDS_FLOW = "funds_flow"
MODEL_TYPE_BALANCE_TRACKING = "balance_tracking"


def get_model_types():
    return [MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING]


class Challenge(BaseModel):
    kind: str = Field(default=MODEL_TYPE_FUNDS_FLOW)
    in_total_amount: Optional[int] = None
    out_total_amount: Optional[int] = None
    tx_id_last_6_chars: Optional[str] = None
    checksum: Optional[str] = None
    block_height: Optional[int] = None
    output: Optional[Dict] = None


class ChallengesResponse(BaseModel):
    funds_flow_challenge_expected: str
    balance_tracking_challenge_expected: int
    funds_flow_challenge_actual: Optional[str]
    balance_tracking_challenge_actual: Optional[int]


class ChallengeMinerResponse(BaseModel):
    network: str

    funds_flow_challenge_expected: str
    balance_tracking_challenge_expected: int
    funds_flow_challenge_actual: Optional[str]
    balance_tracking_challenge_actual: Optional[int]

    def get_failed_challenges(self):
        funds_flow_challenge_passed = self.funds_flow_challenge_expected == self.funds_flow_challenge_actual
        balance_tracking_challenge_passed = self.balance_tracking_challenge_expected == self.balance_tracking_challenge_actual

        failed_challenges = 0
        if funds_flow_challenge_passed is False:
            failed_challenges += 1

        if balance_tracking_challenge_passed is False:
            failed_challenges += 1

        return failed_challenges
