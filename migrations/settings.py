import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

load_dotenv()


class MigrationSettings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    DB_URL_OBJ: URL = URL.create(
        "postgresql+asyncpg",
        username=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT"),
        database=os.environ.get("POSTGRES_DB")
    )

    DATABASE_URL: str = f"{DB_URL_OBJ.drivername}://{DB_URL_OBJ.username}:{DB_URL_OBJ.password}@{DB_URL_OBJ.host}:{DB_URL_OBJ.port}/{DB_URL_OBJ.database}"
    PROJECT_ROOT: Path = Path(__file__).parent.parent.resolve()
    model_config = SettingsConfigDict(env_file=".env", extra='allow')


migration_settings = MigrationSettings()
