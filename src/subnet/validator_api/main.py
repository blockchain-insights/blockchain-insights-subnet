import signal
import uvicorn
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
import sys
from src.subnet.validator_api import patch_record, miner_discovery_manager, settings_manager, settings
from src.subnet.validator_api.rate_limiter import RateLimiterMiddleware
from src.subnet.validator_api.routes.v1.balance_tracking import balance_tracking_router
from src.subnet.validator_api.routes.v1.funds_flow import funds_flow_router
from src.subnet.validator_api.routes.v1.miner_receipts import miner_router

logger.remove()
logger.add(
    "../../logs/validator_api.log",
    rotation="500 MB",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    filter=patch_record
)

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <blue>{message}</blue> | {extra}",
    level="DEBUG",
    filter=patch_record
)

app = FastAPI(
    title="Chain Insights API",
    description="",
    version="0.1.0"
)

app.include_router(funds_flow_router)
app.include_router(balance_tracking_router)
app.include_router(miner_router)
app.add_middleware(RateLimiterMiddleware, redis_url=settings.REDIS_URL, max_requests=settings.API_RATE_LIMIT,
                   window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def shutdown_handler(signal, frame):
    logger.debug("Shutdown handler started")
    settings_manager.stop_reloader()
    uvicorn.should_exit = True
    uvicorn.force_exit = True
    logger.debug("Shutdown handler finished")


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m subnet.validator.validator_api <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)

    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, workers=settings.WORKERS)
