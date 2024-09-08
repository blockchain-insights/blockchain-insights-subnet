from typing import Optional
import json
from decimal import Decimal

from loguru import logger
from sqlalchemy import Column, Integer, String, DateTime, insert, delete
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from datetime import datetime

from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.base_model import to_dict
from src.subnet.validator.database.session_manager import DatabaseSessionManager

import random

Base = declarative_base()

class ChallengeFundsFlow(OrmBase):
    __tablename__ = 'challenge_funds_flow'
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

    async def get_challenge_by_id(self, challenge_id: int):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(ChallengeFundsFlow).where(ChallengeFundsFlow.id == challenge_id)
            )
            return to_dict(result.scalars().first())

    async def get_random_challenge(self, network: str) -> str:
        async with self.session_manager.session() as session:
            min_id_result = await session.execute(
                select(ChallengeFundsFlow.id)
                .where(ChallengeFundsFlow.network == network)
                .order_by(ChallengeFundsFlow.id.asc()).limit(1)
            )
            min_id = min_id_result.scalar()

            max_id_result = await session.execute(
                select(ChallengeFundsFlow.id)
                .where(ChallengeFundsFlow.network == network)
                .order_by(ChallengeFundsFlow.id.desc()).limit(1)
            )
            max_id = max_id_result.scalar()

            if min_id is None or max_id is None:
                return None  # No records found

            random_id = random.randint(min_id, max_id)

            result = await session.execute(
                select(ChallengeFundsFlow)
                .where(ChallengeFundsFlow.id == random_id)
                .where(ChallengeFundsFlow.network == network)
            )
            return to_dict(result.scalars().first())['challenge']

    async def get_challenge_count(self, network: str):
        async with self.session_manager.session() as session:
            result = await session.execute(
                select(func.count(ChallengeFundsFlow.id)).where(ChallengeFundsFlow.network == network)
            )
            return result.scalar()

    async def try_delete_oldest_challenge(self, network: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                oldest_challenge_result = await session.execute(
                    select(ChallengeFundsFlow)
                    .where(ChallengeFundsFlow.network == network)
                    .order_by(ChallengeFundsFlow.created_at.asc()).limit(1)
                )
                oldest_challenge = oldest_challenge_result.scalars().first()

                if oldest_challenge:
                    await session.execute(
                        delete(ChallengeFundsFlow).where(ChallengeFundsFlow.id == oldest_challenge.id)
                    )
                    logger.info(f"Deleted oldest challenge with ID: {oldest_challenge.id}")
