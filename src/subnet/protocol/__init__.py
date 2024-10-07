from typing import Optional, Dict
from pydantic import BaseModel, Field

NETWORK_BITCOIN = "bitcoin"
NETWORK_COMMUNE = "commune"


def get_networks():
    return [NETWORK_COMMUNE, NETWORK_BITCOIN]


class Discovery(BaseModel):
    network: str = Field(NETWORK_BITCOIN, title="The network to discover")
    version: float = Field(1.0, title="The version of the discovery")
    graph_db: str = Field("neo4j", title="The graph database type")


# Model types
MODEL_KIND_FUNDS_FLOW = "funds_flow"
MODEL_KIND_BALANCE_TRACKING = "balance_tracking"


def get_model_kinds():
    return [MODEL_KIND_FUNDS_FLOW, MODEL_KIND_BALANCE_TRACKING]


class Challenge(BaseModel):
    model_kind: str = Field(default=MODEL_KIND_FUNDS_FLOW)
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
    version: float
    graph_db: str

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
