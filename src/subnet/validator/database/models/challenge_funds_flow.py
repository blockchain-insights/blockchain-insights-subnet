from typing import Tuple
from sqlalchemy import Column, Integer, String, DateTime, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from sqlalchemy import text
from datetime import datetime

from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.session_manager import DatabaseSessionManager
from loguru import logger

Base = declarative_base()

class ChallengeFundsFlow(OrmBase):
    __tablename__ = 'challenges_funds_flow'
    id = Column(Integer, primary_key=True, autoincrement=True)
    challenge = Column(String, nullable=False)
    tx_id = Column(String, nullable=False, unique=True)
    network = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ChallengeFundsFlowManager:
    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager

    async def store_challenge(self, challenge: str, tx_id: str, network: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(ChallengeFundsFlow).values(
                    challenge=challenge,
                    tx_id=tx_id,
                    network=network,
                    created_at=datetime.utcnow()  # Automatically set the created_at field
                ).on_conflict_do_update(
                    index_elements=['tx_id'],  # Conflict on tx_id
                    set_=dict(
                        challenge=challenge,
                        network=network,
                        created_at=datetime.utcnow()  # Update these fields on conflict
                    )
                )
                await session.execute(stmt)

    async def get_random_challenge(self, network: str) -> Tuple[str, str]:
        async with self.session_manager.session() as session:
            query = text("""
                SELECT challenge, tx_id 
                FROM challenges_funds_flow 
                WHERE network = :network 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            result = await session.execute(query, {"network": network})
            row = result.fetchone()

            if row:
                # Access tuple values by index
                return row[0], row[1]
            return None, None

    async def get_challenge_count(self, network: str):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(func.count(ChallengeFundsFlow.id)).where(ChallengeFundsFlow.network == network)
            )
            return result.scalar()

    async def try_delete_oldest_challenge(self, network: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                # Raw SQL query to delete the oldest challenge and return the deleted ID
                query = text("""
                    DELETE FROM challenges_funds_flow
                    WHERE id = (
                        SELECT id FROM challenges_funds_flow
                        WHERE network = :network
                        ORDER BY created_at ASC
                        LIMIT 1
                    )
                    RETURNING id
                """)
                result = await session.execute(query, {"network": network})
                deleted_id = result.fetchone()

                if deleted_id:
                    logger.info(f"Deleted oldest challenge with ID: {deleted_id[0]}")
