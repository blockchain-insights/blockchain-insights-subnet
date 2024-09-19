import json
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, insert, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy import text
from datetime import datetime

from sqlalchemy.orm import relationship, joinedload

from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from loguru import logger

Base = declarative_base()

class ValidationPrompt(OrmBase):
    __tablename__ = 'validation_prompts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    prompt_model_type = Column(String, nullable=False)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    network = Column(String, nullable=False)

    # Use back_populates to explicitly define the relationship
    responses = relationship("ValidationPromptResponse", back_populates="validation_prompt", cascade="all, delete", lazy="joined")


class ValidationPromptManager:
    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager

    def _convert_decimals_to_strings(self, data):
        if isinstance(data, dict):
            return {k: self._convert_decimals_to_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals_to_strings(v) for v in data]
        elif isinstance(data, Decimal):
            return str(data)
        return data

    async def store_prompt(self, prompt: str, prompt_model_type: str, data: dict, network: str):
        data_json = json.dumps(self._convert_decimals_to_strings(data))
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(ValidationPrompt).values(
                    prompt=prompt,
                    prompt_model_type=prompt_model_type,
                    data=data_json,
                    network=network,
                    created_at=datetime.utcnow()
                )
                await session.execute(stmt)

    async def get_random_prompt(self, network: str):
        """
        Fetches a random validation prompt and eagerly loads its associated responses in one DB roundtrip.
        """
        async with self.session_manager.session() as session:
            stmt = (
                select(ValidationPrompt)
                .options(joinedload(ValidationPrompt.responses))  # Eagerly load responses
                .where(ValidationPrompt.network == network)
                .order_by(func.random())  # Get a random prompt
                .limit(1)
            )

            result = await session.execute(stmt)
            validation_prompt = result.scalars().first()

            if validation_prompt:
                return (
                    validation_prompt.id,
                    validation_prompt.prompt,
                    validation_prompt.prompt_model_type,
                    validation_prompt.responses
                )

            return None, None, None

    async def get_prompt_count(self, network: str):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(func.count(ValidationPrompt.id)).where(ValidationPrompt.network == network)
            )
            return result.scalar()

    async def try_delete_oldest_prompt(self, network: str):
        async with self.session_manager.session() as session:
            query = text("""
                DELETE FROM validation_prompts
                WHERE id = (
                    SELECT id 
                    FROM validation_prompts
                    WHERE network = :network
                    ORDER BY created_at ASC
                    LIMIT 1
                )
                RETURNING id
            """)
            result = await session.execute(query, {"network": network})
            deleted_id = result.fetchone()

            if deleted_id:
                logger.info(f"Deleted oldest prompt with ID: {deleted_id[0]}")
