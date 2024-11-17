from src.sdk.chaininsights.api import FundsFlowAPI, BalanceTrackingAPI, MinersAPI
from src.sdk.chaininsights.config import Config


class ChainInsightsSDK:
    """
    Main SDK for accessing ChainInsights API endpoints.
    """
    def __init__(self, base_url: str, api_key: str):
        config = Config(base_url=base_url, api_key=api_key)
        self.funds_flow = FundsFlowAPI(config)
        self.balance_tracking = BalanceTrackingAPI(config)
        self.miners = MinersAPI(config)
