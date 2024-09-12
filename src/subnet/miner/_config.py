from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import sys
import os

from src.subnet.miner.logger import logger


def load_environment(env: str):
    logger.debug(f"Current python interpreter execution path: {sys.executable}")
    if env == 'mainnet':
        dotenv_path = os.path.abspath('../env/.env.miner.mainnet')
    elif env == 'testnet':
        dotenv_path = os.path.abspath('../env/.env.miner.testnet')
    else:
        raise ValueError(f"Unknown environment: {env}")

    logger.debug(f"Loading environment from: {dotenv_path}")
    env_file_found = os.path.exists(dotenv_path)
    logger.debug(f"Environment file found: {env_file_found}")

    load_dotenv(dotenv_path=dotenv_path)


class MinerSettings(BaseSettings):
    NET_UID: int
    MINER_KEY: str
    MINER_NAME: str
    NETWORK: str

    PORT: int = 9962
    WORKERS: int = 4

    LLM_TYPE: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_URL: str

    GRAPH_DATABASE_USER: str
    GRAPH_DATABASE_PASSWORD: str
    GRAPH_DATABASE_URL: str

    LLM_API_KEY: str

    class Config:
        extra = 'ignore'
