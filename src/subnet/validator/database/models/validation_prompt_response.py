from sqlalchemy.orm import relationship
from loguru import logger
from sqlalchemy import Column, Integer, String, insert, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
from src.subnet.validator.database import OrmBase


Base = declarative_base()

class ValidationPromptResponse(OrmBase):
    __tablename__ = 'validation_prompt_response'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, ForeignKey('validation_prompt.id', ondelete='CASCADE'), nullable=False)
    miner_key = Column(String, nullable=False)
    query = Column(String, nullable=False)
    result = Column(Text, nullable=False)
    is_valid = Column(Boolean, nullable=False)

    validation_prompt = relationship("ValidationPrompt", back_populates="responses")


class ValidationPromptResponseManager:
    def __init__(self, session_manager):
        self.session_manager = session_manager

    async def store_response(self, prompt_id: int, miner_key: str, query: str, result: str, is_valid: bool):
        """
        Stores a new validation prompt response.
        Retrieves the prompt ID based on the prompt text and stores the corresponding response.
        """
        async with self.session_manager.session() as session:
            async with session.begin():
                prompt_query = text("""
                    SELECT id 
                    FROM validation_prompt 
                    WHERE id = :prompt_id 
                    LIMIT 1
                """)
                res = await session.execute(prompt_query, {"prompt_id": prompt_id})
                prompt_id = res.scalar()  # Extract the prompt ID

                if not prompt_id:
                    logger.error("No prompt found for the given text")
                    return

                stmt = insert(ValidationPromptResponse).values(
                    prompt_id=prompt_id,
                    miner_key=miner_key,
                    query=query,
                    result=result,
                    is_valid=is_valid
                )
                await session.execute(stmt)