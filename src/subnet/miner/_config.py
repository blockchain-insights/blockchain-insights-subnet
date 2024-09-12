from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os


def load_environment(env: str):
    if env == 'mainnet':
        dotenv_path = os.path.abspath('../env/.env.miner.mainnet')
    elif env == 'testnet':
        dotenv_path = os.path.abspath('../env/.env.miner.testnet')
    else:
        raise ValueError(f"Unknown environment: {env}")

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
