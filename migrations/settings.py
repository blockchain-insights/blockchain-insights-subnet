from pydantic_settings import BaseSettings, SettingsConfigDict


class MigrationSettings(BaseSettings):
    DATABASE_URL: str
    model_config = SettingsConfigDict(extra='allow')
