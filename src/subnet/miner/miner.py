from datetime import datetime
from typing import Optional
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.module import Module, endpoint
from communex.module._rate_limiters.limiters import IpLimiterParams
from keylimiter import TokenBucketLimiter
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from substrateinterface import Keypair
from src.subnet import VERSION
from src.subnet.encryption import generate_hash
from src.subnet.miner._config import MinerSettings, load_environment
from src.subnet.miner.balance_search import BalanceSearch
from src.subnet.miner.graph_search import GraphSearch
from src.subnet.protocol import MODEL_KIND_MONEY_FLOW_LIVE, MODEL_KIND_MONEY_FLOW_ARCHIVE, MODEL_KIND_BALANCE_TRACKING, \
    MODEL_KIND_TRANSACTION_STREAM
from src.subnet.validator.database import db_manager


class Miner(Module):

    def __init__(self, keypair: Keypair, settings: MinerSettings):
        super().__init__()
        self.keypair = keypair
        self.settings = settings

        self.graph_search_live = GraphSearch(graph_database_url=self.settings.MONEY_FLOW_MEMGRAPH_LIVE_URL,
                                             graph_database_user=self.settings.MONEY_FLOW_MEMGRAPH_LIVE_USER,
                                             graph_database_password=self.settings.MONEY_FLOW_MEMGRAPH_LIVE_PASSWORD)

        self.graph_search_archive = GraphSearch(graph_database_url=self.settings.MONEY_FLOW_MEMGRAPH_ARCHIVE_URL,
                                                graph_database_user=self.settings.MONEY_FLOW_MEMGRAPH_ARCHIVE_USER,
                                                graph_database_password=self.settings.MONEY_FLOW_MEMGRAPH_ARCHIVE_PASSWORD)

    @endpoint
    async def discovery(self, validator_version: str, validator_key: str) -> dict:
        logger.debug(f"Received discovery request from {validator_key}", validator_key=validator_key)

        if float(validator_version) != VERSION:
            logger.error(f"Invalid validator version: {validator_version}, expected: {VERSION}")
            raise ValueError(f"Invalid validator version: {validator_version}, expected: {VERSION}")

        return {
            "network": self.settings.NETWORK,
            "version": VERSION
        }

    @endpoint
    async def query(self, model_kind: str, query: str, validator_key: str, args: Optional[str]) -> dict:

        logger.debug(f"Received query request from {validator_key}", validator_key=validator_key)

        try:
            result = None

            if model_kind == MODEL_KIND_MONEY_FLOW_ARCHIVE:
                result = self.graph_search_archive.execute_query(query)
                response_hash = generate_hash(str(result))
                result_hash_signature = self.keypair.sign(response_hash).hex()
                return {
                    "result": result,
                    "result_hash_signature": result_hash_signature,
                    "result_hash": response_hash
                }

            if args == MODEL_KIND_MONEY_FLOW_LIVE:
                result = self.graph_search_live.execute_query(query)
                response_hash = generate_hash(str(result))
                result_hash_signature = self.keypair.sign(response_hash).hex()
                return {
                    "result": result,
                    "result_hash_signature": result_hash_signature,
                    "result_hash": response_hash
                }

            elif model_kind == MODEL_KIND_BALANCE_TRACKING or model_kind == MODEL_KIND_TRANSACTION_STREAM:
                search = BalanceSearch()
                result = await search.execute_query(query)
                response_hash = generate_hash(str(result))
                result_hash_signature = self.keypair.sign(response_hash).hex()

                return {
                    "result": result,
                    "result_hash_signature": result_hash_signature,
                    "result_hash": response_hash
                }
            else:
                raise ValueError(f"Invalid model type: {model_kind}")
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    from communex.module.server import ModuleServer
    from communex.compat.key import classic_load_key
    import uvicorn
    import time
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m subnet.cli <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)

    env = sys.argv[1]
    use_testnet = env == 'testnet'
    load_environment(env)

    settings = MinerSettings()
    keypair = classic_load_key(settings.MINER_KEY)

    def patch_record(record):
        record["extra"]["miner_key"] = keypair.ss58_address
        record["extra"]["service"] = 'miner'
        record["extra"]["timestamp"] = datetime.utcnow().isoformat()
        record["extra"]["level"] = record['level'].name

        return True

    logger.remove()
    logger.add(
        "../logs/miner.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}",
        filter=patch_record
    )

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <blue>{message}</blue> | {extra}",
        level="DEBUG",
        filter = patch_record
    )

    c_client = CommuneClient(get_node_url(use_testnet=use_testnet))
    miner = Miner(keypair=keypair, settings=settings)
    refill_rate: float = 1 / 1000
    bucket = TokenBucketLimiter(
        refill_rate=refill_rate,
        bucket_size=1000,
        time_func=time.time,
    )
    limiter = IpLimiterParams()
    db_manager.init(settings.TIMESERIES_DB_CONNECTION_STRING)

    server = ModuleServer(miner,
                          keypair,
                          subnets_whitelist=[settings.NET_UID],
                          use_testnet=use_testnet,
                          limiter=limiter)

    app = server.get_fastapi_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
