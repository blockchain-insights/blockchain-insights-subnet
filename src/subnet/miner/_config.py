from pydantic_settings import BaseSettings
from dotenv import load_dotenv


def load_environment(env: str):
    if env == 'mainnet':
        load_dotenv(dotenv_path='../env/.env.miner.mainnet')
    elif env == 'testnet':
        load_dotenv(dotenv_path='../env/.env.miner.testnet')
    else:
        raise ValueError(f"Unknown environment: {env}")


class MinerSettings(BaseSettings):
    NET_UID: int
    MINER_KEY: str
    MINER_NAME: str
    NETWORK: str

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
        env_file = '../env/.env.miner.testnet'  # Default .env file
        extra = 'ignore'
