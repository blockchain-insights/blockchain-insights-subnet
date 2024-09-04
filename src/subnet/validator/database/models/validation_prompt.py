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

    async def store_prompt(self, prompt: str, block: dict):
        # Convert the block dictionary to a JSON string, converting Decimal to strings
        block_json = json.dumps(self._convert_decimals_to_strings(block))

        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(ValidationPrompt).values(
                    prompt=prompt,
                    block=block_json,
                    created_at=datetime.utcnow()  # Automatically set the created_at field
                )
                await session.execute(stmt)

    async def get_prompt_by_id(self, prompt_id: int):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(ValidationPrompt).where(ValidationPrompt.id == prompt_id)
            )
            return to_dict(result.scalars().first())

    async def get_random_prompt(self) -> str:
        async with self.session_manager.session() as session:
            # First, get the min and max ID in the table
            min_id_result = await session.execute(
                select(ValidationPrompt.id).order_by(ValidationPrompt.id.asc()).limit(1)
            )
            min_id = min_id_result.scalar()

            max_id_result = await session.execute(
                select(ValidationPrompt.id).order_by(ValidationPrompt.id.desc()).limit(1)
            )
            max_id = max_id_result.scalar()

            if min_id is None or max_id is None:
                return None  # No records found

            # Generate a random ID within the range
            random_id = random.randint(min_id, max_id)

            # Retrieve the prompt with the random ID
            result = await session.execute(
                select(ValidationPrompt).where(ValidationPrompt.id == random_id)
            )
            return to_dict(result.scalars().first())['prompt']

    async def get_prompt_count(self):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(func.count(ValidationPrompt.id))
            )
            return result.scalar()

    async def try_delete_oldest_prompt(self):
        async with self.session_manager.session() as session:
            async with session.begin():
                # Get the oldest prompt (with the lowest ID or oldest created_at timestamp)
                oldest_prompt_result = await session.execute(
                    select(ValidationPrompt).order_by(ValidationPrompt.created_at.asc()).limit(1)
                )
                oldest_prompt = oldest_prompt_result.scalars().first()

                if oldest_prompt:
                    # Delete the oldest prompt
                    await session.execute(
                        delete(ValidationPrompt).where(ValidationPrompt.id == oldest_prompt.id)
                    )
                    logger.info(f"Deleted oldest prompt with ID: {oldest_prompt.id}")