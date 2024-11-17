from typing import Optional
from pydantic import BaseSettings


class Config(BaseSettings):
    base_url: str
    api_key: str

    class Config:
        env_prefix = "SDK_"
