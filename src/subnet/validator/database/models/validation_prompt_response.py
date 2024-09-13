from typing import Optional

from sqlalchemy.orm import relationship, joinedload

from loguru import logger
from sqlalchemy import Column, Integer, String, Float, DateTime, update, insert, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from src.subnet.validator.database import OrmBase, ValidationPrompt
from src.subnet.validator.database.session_manager import DatabaseSessionManager


Base = declarative_base()

class ValidationPromptResponse(OrmBase):
    __tablename__ = 'validation_prompt_response'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, ForeignKey('validation_prompt.id', ondelete='CASCADE'), nullable=False)
    miner_key = Column(String, nullable=False)
    query = Column(String, nullable=False)
    result = Column(String, nullable=False)

    # Explicitly define the relationship with back_populates
    validation_prompt = relationship("ValidationPrompt", back_populates="responses")


class ValidationPromptResponseManager:
    def __init__(self, session_manager):
        self.session_manager = session_manager

    async def store_response(self, prompt: str, miner_key: str, query: str, result: str):
        """
        Stores a new validation prompt response.
        Retrieves the prompt ID based on the prompt text and stores the corresponding response.
        """
        async with self.session_manager.session() as session:
            async with session.begin():
                # Retrieve the prompt_id based on the prompt text using raw SQL
                prompt_query = text("""
                    SELECT id 
                    FROM validation_prompt 
                    WHERE prompt = :prompt 
                    LIMIT 1
                """)
                res = await session.execute(prompt_query, {"prompt": prompt})
                prompt_id = res.scalar()  # Extract the prompt ID

                if not prompt_id:
                    logger.error("No prompt found for the given text")
                    return

                # Insert the response with the retrieved prompt_id
                stmt = insert(ValidationPromptResponse).values(
                    prompt_id=prompt_id,
                    miner_key=miner_key,
                    query=query,
                    result=result,
                )
                await session.execute(stmt)

    async def get_response_by_prompt_and_miner(self, prompt: str, miner_key: str) -> Optional[str]:
        """
        Retrieves the response query for a given miner_key and prompt text.
        Returns the query string if found, otherwise None.
        """
        async with self.session_manager.session() as session:
            # Retrieve the prompt and its responses using eager loading
            prompt_query = await session.execute(
                select(ValidationPrompt)
                .options(joinedload(ValidationPrompt.responses))
                .where(ValidationPrompt.prompt == prompt)
            )
            validation_prompt = prompt_query.scalars().first()

            if not validation_prompt:
                logger.error(f"No prompt found for the given text: {prompt}")
                return None

            # Retrieve the single response associated with this prompt_id and miner_key
            response = next(
                (resp.query for resp in validation_prompt.responses if resp.miner_key == miner_key),
                None
            )

            return response if response else None
