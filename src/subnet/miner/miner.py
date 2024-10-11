import signal
from datetime import datetime
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.module import Module, endpoint
from communex.module._rate_limiters.limiters import IpLimiterParams
from keylimiter import TokenBucketLimiter
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from src.subnet import VERSION
from src.subnet.miner._config import MinerSettings, load_environment
from src.subnet.miner.blockchain.search import GraphSearchFactory, BalanceSearchFactory
from src.subnet.protocol import Challenge, MODEL_KIND_FUNDS_FLOW, MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator.database import db_manager


class Miner(Module):

    def __init__(self, settings: MinerSettings):
        super().__init__()
        self.settings = settings
        self.graph_search_factory = GraphSearchFactory()
        self.balance_search_factory = BalanceSearchFactory()

    @endpoint
    async def discovery(self, validator_version: str, validator_key: str) -> dict:
        """
        Returns the network, version and graph database type of the miner
        Returns:
            dict: The network of the miner
            {
                "network": "bitcoin",
                "version": 1.0,
                "graph_db": "neo4j"
            }
        """

        logger.debug(f"Received discovery request from {validator_key}", validator_key=validator_key)

        if float(validator_version) != VERSION:
            logger.error(f"Invalid validator version: {validator_version}, expected: {VERSION}")
            raise ValueError(f"Invalid validator version: {validator_version}, expected: {VERSION}")

        return {
            "network": self.settings.NETWORK,
            "version": VERSION,
            "graph_db": self.settings.GRAPH_DB_TYPE
        }

    @endpoint
    async def query(self, model_kind: str, query: str, validator_key: str) -> dict:

        logger.debug(f"Received challenge request from {validator_key}", validator_key=validator_key)

        try:

            if model_kind == MODEL_KIND_FUNDS_FLOW:
                search = GraphSearchFactory().create_graph_search(self.settings)
                result = search.execute_query(query)
                return result

            elif model_kind == MODEL_KIND_BALANCE_TRACKING:
                search = BalanceSearchFactory().create_balance_search(self.settings.NETWORK)
                result = await search.execute_query(query)
                return result
            else:
                raise ValueError(f"Invalid model type: {model_kind}")
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}

    @endpoint
    async def challenge(self, challenge: Challenge, validator_key: str) -> Challenge:
        """
        Solves the challenge and returns the output
        Args:
            validator_key:
            challenge: {
                "model_kind": "funds_flow",
                "in_total_amount": 0.0,
                "out_total_amount": 0.0,
                "tx_id_last_6_chars": "string",
                "checksum": "string",
                "block_height": 0
            }

        Returns:
            dict: The output of the challenge
            {
                "output": "tx_id|sum"
            }

        """

        logger.debug(f"Received challenge request from {validator_key}", validator_key=validator_key)

        challenge = Challenge(**challenge)

        if challenge.model_kind == MODEL_KIND_FUNDS_FLOW:
            search = GraphSearchFactory().create_graph_search(self.settings)
            tx_id = search.solve_challenge(
                in_total_amount=challenge.in_total_amount,
                out_total_amount=challenge.out_total_amount,
                tx_id_last_6_chars=challenge.tx_id_last_6_chars
            )

            challenge.output = {'tx_id': tx_id}
            return challenge
        else:
            search = BalanceSearchFactory().create_balance_search(self.settings.NETWORK)
            challenge.output = {
                'balance': await search.solve_challenge([challenge.block_height])
            }
            return challenge


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
    miner = Miner(settings=settings)
    refill_rate: float = 1 / 1000
    bucket = TokenBucketLimiter(
        refill_rate=refill_rate,
        bucket_size=1000,
        time_func=time.time,
    )
    limiter = IpLimiterParams()
    db_manager.init(settings.DATABASE_URL)

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

    def shutdown_handler(signal, frame):
        uvicorn_server.should_exit = True
        uvicorn_server.force_exit = True

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    uvicorn_server = uvicorn.Server(config=uvicorn.Config(app, host="0.0.0.0", port=settings.PORT, workers=settings.WORKERS))
    uvicorn_server.run()
