from pydantic_settings import BaseSettings
from dotenv import load_dotenv


def load_environment(env: str):
    if env == 'mainnet':
        load_dotenv(dotenv_path='../env/.env.validator.mainnet')
    elif env == 'testnet':
        load_dotenv(dotenv_path='../env/.env.validator.testnet')
    else:
        raise ValueError(f"Unknown environment: {env}")


class ValidatorSettings(BaseSettings):
    ITERATION_INTERVAL: int
    MAX_ALLOWED_WEIGHTS: int
    NET_UID: int
    VALIDATOR_KEY: str

    WEIGHTS_FILE_NAME: str = 'weights.pkl'
    DATABASE_URL: str
    API_RATE_LIMIT: int
    REDIS_URL: str

    LLM_QUERY_TIMEOUT: int  # llm query timeout (organic prompt)
    QUERY_TIMEOUT: int   # cross check query timeout
    CHALLENGE_TIMEOUT: int  # challenge and llm challenge time

    LLM_API_KEY: str
    LLM_TYPE: str

    class Config:
        env_file = '../env/.env.validator.testnet'  # Default .env file
        extra = 'ignore'
