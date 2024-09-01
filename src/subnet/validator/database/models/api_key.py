from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, select
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.session_manager import DatabaseSessionManager

Base = declarative_base()


class ApiKey(OrmBase):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(String, nullable=True)


class ApiKeyManager:
    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager

    async def validate_api_key(self, key: Optional[str] = None):
        async with self.session_manager.session() as session:
            if key is None:
                # Check if there are any API keys in the database
                result = await session.execute(select(ApiKey.id).limit(1))
                api_key_exists = result.scalars().first() is not None
                return not api_key_exists  # Allow access if no API keys are present

            # Check if the provided key is valid and enabled
            result = await session.execute(
                select(ApiKey).where(ApiKey.key == key, ApiKey.enabled == True)
            )
            return result.scalars().first() is not None