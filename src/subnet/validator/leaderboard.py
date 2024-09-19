import json
import signal
from datetime import datetime

import uvicorn
from communex.compat.key import classic_load_key
from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.websockets import WebSocketDisconnect
import asyncio

from src.subnet.validator._config import ValidatorSettings, load_environment, SettingsManager
from src.subnet.validator.database.models.miner_discovery import MinerDiscoveryManager
from src.subnet.validator.database.models.miner_receipt import MinerReceiptManager
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from src.subnet.validator.rate_limiter import RateLimiterMiddleware


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m subnet.validator.leaderboard <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)

    env = sys.argv[1]
    use_testnet = env == 'testnet'
    load_environment(env)

    settings_manager = SettingsManager.get_instance()
    settings = settings_manager.get_settings()
    keypair = classic_load_key(settings.VALIDATOR_KEY)

    def patch_record(record):
        record["extra"]["validator_key"] = keypair.ss58_address
        record["extra"]["service"] = 'leaderboard'
        record["extra"]["timestamp"] = datetime.utcnow().isoformat()
        record["extra"]["level"] = record['level'].name

        return True


    logger.remove()
    logger.add(
        "../../logs/leaderboard.log",
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

    session_manager = DatabaseSessionManager()
    session_manager.init(settings.DATABASE_URL)

    miner_discovery_manager = MinerDiscoveryManager(session_manager)
    miner_receipt_manager = MinerReceiptManager(session_manager)

    app = FastAPI(title="Leaderboard", description="Leaderboard for Subnet Miners")
    app.add_middleware(RateLimiterMiddleware,
                       redis_url=settings.REDIS_URL,
                       max_requests=settings.API_RATE_LIMIT,
                       window_seconds=60)
    templates = Jinja2Templates(directory="subnet/validator/templates")
    app.mount("/static", StaticFiles(directory="subnet/validator/static"), name="static")


    @app.get("/")
    async def get_dashboard(request: Request):
        return templates.TemplateResponse("leaderboard.html", {"request": request})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await miner_discovery_manager.get_miners_for_leader_board()
                json_data = json.dumps(data)

                logger.debug(f"Sending data: {data}")
                await websocket.send_json(data)
                await asyncio.sleep(10000000000)
        except WebSocketDisconnect:
            logger.error("WebSocket connection closed")


    def shutdown_handler(signal, frame):
        logger.debug("Shutdown handler started")
        uvicorn_server.should_exit = True
        uvicorn_server.force_exit = True
        logger.debug("Shutdown handler finished")

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    uvicorn_server = uvicorn.Server(config=uvicorn.Config(app, host="0.0.0.0", port=settings.PORT + 1, workers=settings.WORKERS))
    uvicorn_server.run()