from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
import sys
from src.subnet.gateway import patch_record, settings, receipt_sync_fetch_thread, validator
from src.subnet.gateway.routes.v1.balance_tracking import balance_tracking_router
from src.subnet.gateway.routes.v1.money_flow import money_flow_router
from src.subnet.gateway.routes.v1.miners import miner_router

logger.remove()
logger.add(
    "../../logs/gateway.log",
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    receipt_sync_fetch_thread.start()
    logger.info("Gateway sync started successfully.")
    yield
    # Shutdown
    logger.info("Initiating graceful shutdown...")
    if validator and receipt_sync_fetch_thread:
        validator.terminate_event.set()
        receipt_sync_fetch_thread.join()
        logger.info("Gateway sync stopped successfully.")

app = FastAPI(
    lifespan=lifespan,
    title="The Chain Insights Gateway",
    description="",
    version="0.1.0"
)

app.include_router(money_flow_router)
app.include_router(balance_tracking_router)
app.include_router(miner_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m subnet.validator.gateway <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, workers=settings.WORKERS)
    except KeyboardInterrupt as e:
        logger.info("Received shutdown signal")
    finally:
        logger.info("Server shutdown complete")

