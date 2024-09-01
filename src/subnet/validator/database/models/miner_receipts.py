from dataclasses import dataclass
from typing import List, Optional, Dict

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, update, insert, BigInteger, Boolean, UniqueConstraint, Text, select, \
    func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import case
from datetime import datetime, timedelta
from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.session_manager import DatabaseSessionManager

Base = declarative_base()


class MinerReceipt(OrmBase):
    __tablename__ = 'miner_receipts'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=False)
    miner_key = Column(String, nullable=False)
    prompt_hash = Column(Text, nullable=False)
    accepted = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('miner_key', 'request_id', name='uq_miner_key_request_id'),
    )


class ReceiptMinerRank(BaseModel):
    miner_ratio: float
    miner_rank: int


class MinerReceiptManager:
    def __init__(self, session_manager: DatabaseSessionManager):
        self.session_manager = session_manager

    async def store_miner_receipt(self, request_id: str, miner_key: str, prompt_hash: str, timestamp: datetime):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(MinerReceipt).values(
                    request_id=request_id,
                    miner_key=miner_key,
                    prompt_hash=prompt_hash,
                    accepted=False,
                    timestamp=timestamp
                )
                await session.execute(stmt)

    async def accept_miner_receipt(self, request_id: str, miner_key: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = update(MinerReceipt).where(
                    (MinerReceipt.request_id == request_id) & (MinerReceipt.miner_key == miner_key)
                ).values(accepted=True)
                await session.execute(stmt)

    async def get_receipts_by_miner_key(self, miner_key: str, page: int = 1, page_size: int = 10):
        async with self.session_manager.session() as session:
            # Calculate offset
            offset = (page - 1) * page_size

            # Query total number of receipts
            total_items_result = await session.execute(
                select(func.count(MinerReceipt.id))
                .where(MinerReceipt.miner_key == miner_key)
            )
            total_items = total_items_result.scalar()

            # Calculate total pages
            total_pages = (total_items + page_size - 1) // page_size

            # Query paginated receipts
            result = await session.execute(
                select(MinerReceipt)
                .where(MinerReceipt.miner_key == miner_key)
                .order_by(MinerReceipt.timestamp.desc())
                .limit(page_size)
                .offset(offset)
            )
            receipts = result.scalars().all()

            return {
                "receipts": receipts,
                "total_pages": total_pages,
                "total_items": total_items
            }

    async def get_receipt_miner_rank(self) -> List[ReceiptMinerRank]:
        async with self.session_manager.session() as session:
            query = text("""
                            WITH miner_ratios AS (
                                SELECT 
                                    miner_key,
                                    COUNT(CASE WHEN accepted = True THEN 1 END) AS accepted_true_count,
                                    COUNT(CASE WHEN accepted = False THEN 1 END) AS accepted_false_count,
                                    CASE 
                                        WHEN COUNT(CASE WHEN accepted = False THEN 1 END) = 0 
                                        THEN NULL 
                                        ELSE COUNT(CASE WHEN accepted = True THEN 1 END)::float / COUNT(CASE WHEN accepted = False THEN 1 END)
                                    END AS ratio
                                FROM 
                                    miner_receipts
                                WHERE 
                                    timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                                GROUP BY 
                                    miner_key
                            )
                            SELECT 
                                miner_key,
                                ratio,
                                RANK() OVER (ORDER BY ratio DESC NULLS LAST) AS rank
                            FROM 
                                miner_ratios
                        """)

            result = await session.execute(query).fetchone()
            result = [ReceiptMinerRank(miner_ratio=row['ratio'], miner_rank=row['rank']) for row in result]

            return result

    async def get_receipt_miner_multiplier(self, miner_key: Optional[str] = None) -> List[Dict[str, float]] | float:
        async with self.session_manager.session() as session:
            query = text("""
                WITH total_receipts AS (
                    SELECT COUNT(*) AS total_count
                    FROM miner_receipts
                    WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                ),
                miner_accepted_counts AS (
                    SELECT 
                        miner_key,
                        COUNT(CASE WHEN accepted = True THEN 1 END) AS accepted_true_count
                    FROM 
                        miner_receipts
                    WHERE 
                        timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                        {miner_key_filter}
                    GROUP BY 
                        miner_key
                )
                SELECT 
                    mac.miner_key,
                    CASE 
                        WHEN tr.total_count = 0 THEN NULL  -- or you can use 0 instead of NULL
                        ELSE POWER(mac.accepted_true_count::float / tr.total_count, 2)
                    END AS multiplier
                FROM 
                    miner_accepted_counts mac, total_receipts tr
                ORDER BY multiplier DESC;
            """.format(miner_key_filter="AND miner_key = :miner_key" if miner_key else ""))

            params = {'miner_key': miner_key} if miner_key else {}
            result = await session.execute(query, params)

            if miner_key is not None:
                result = result.fetchone()
                if result is None:
                    return 0.0
                return result[1]

            return [dict(row) for row in result.fetchall()]
