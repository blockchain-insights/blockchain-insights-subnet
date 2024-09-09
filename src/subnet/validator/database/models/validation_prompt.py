from typing import Optional
import json
from decimal import Decimal

from loguru import logger
from sqlalchemy import Column, Integer, String, Float, DateTime, update, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import text
from datetime import datetime

from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.base_model import to_dict
from src.subnet.validator.database.session_manager import DatabaseSessionManager

import random

Base = declarative_base()

class ValidationPrompt(OrmBase):
    __tablename__ = 'validation_prompt'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(String, nullable=False)
    block = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    network = Column(String, nullable=False)

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

    async def store_prompt(self, prompt: str, block: dict, network: str):
        # Convert the block dictionary to a JSON string, converting Decimal to strings
        block_json = json.dumps(self._convert_decimals_to_strings(block))

        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(ValidationPrompt).values(
                    prompt=prompt,
                    block=block_json,
                    network=network,  # Add the network to the insert statement
                    created_at=datetime.utcnow()  # Automatically set the created_at field
                )
                await session.execute(stmt)

    async def get_random_prompt(self, network: str) -> str:
        async with self.session_manager.session() as session:
            query = text("""
                   SELECT prompt 
                   FROM validation_prompt
                   WHERE network = :network
                   ORDER BY RANDOM() 
                   LIMIT 1
               """)
            result = await session.execute(query, {"network": network})
            prompt_data = result.fetchone()

            if prompt_data:
                return prompt_data[0]
            return None

    async def get_prompt_count(self, network: str):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(func.count(ValidationPrompt.id)).where(ValidationPrompt.network == network)
            )
            return result.scalar()

    async def try_delete_oldest_prompt(self, network: str):
        async with self.session_manager.session() as session:
            query = text("""
                DELETE FROM validation_prompt
                WHERE id = (
                    SELECT id 
                    FROM validation_prompt
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
