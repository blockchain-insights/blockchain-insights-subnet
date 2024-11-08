from typing import List, Optional, Dict, Union
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, update, insert, BigInteger, Boolean, UniqueConstraint, Text, select, \
    func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from src.subnet.validator.database import OrmBase
from src.subnet.validator.database.session_manager import DatabaseSessionManager

Base = declarative_base()


class MinerReceipt(OrmBase):
    __tablename__ = 'miner_receipts'
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    validator_key = Column(String, nullable=False)
    is_local_receipt = Column(Boolean, nullable=False, default=True)


    request_id = Column(String, nullable=False)
    miner_key = Column(String, nullable=False)
    model_kind = Column(String, nullable=False)
    network = Column(String, nullable=False)
    query_hash = Column(Text, nullable=False)
    response_hash = Column(Text, nullable=False)
    response_accepted = Column(Boolean, nullable=False, default=False)
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

    async def store_miner_receipt(self, validator_key: str, request_id: str, miner_key: str, model_kind: str, network: str, query_hash: str, timestamp: datetime, response_hash: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(MinerReceipt).values(
                    request_id=request_id,
                    miner_key=miner_key,
                    model_kind=model_kind,
                    query_hash=query_hash,
                    network=network,
                    response_accepted=False,
                    timestamp=timestamp,
                    response_hash=response_hash,
                    is_local_receipt=True,
                    validator_key=validator_key
                )
                await session.execute(stmt)

    async def sync_miner_receipts(self, receipts: List[Dict[str, Union[str, datetime, bool]]]):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(MinerReceipt).values(receipts).on_conflict_do_nothing(
                    index_elements=['miner_key', 'request_id'])
                await session.execute(stmt)

    async def sync_miner_receipt(self, validator_key: str, request_id: str, miner_key: str, model_kind: str, network: str, query_hash: str,
                                  timestamp: datetime, response_hash: str, response_accepted: bool):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(MinerReceipt).values(
                    request_id=request_id,
                    miner_key=miner_key,
                    model_kind=model_kind,
                    query_hash=query_hash,
                    network=network,
                    response_accepted=response_accepted,
                    timestamp=timestamp,
                    response_hash=response_hash,
                    is_local_receipt=False,
                    validator_key=validator_key
                ).on_conflict_do_nothing(index_elements=['miner_key', 'request_id'])
                await session.execute(stmt)

    async def accept_miner_receipt(self, request_id: str, miner_key: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = update(MinerReceipt).where(
                    MinerReceipt.request_id == request_id
                ).where(
                    MinerReceipt.miner_key == miner_key
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
                "data": receipts,
                "total_pages": total_pages,
                "total_items": total_items
            }

    async def get_receipts_by_to_sync(self, timestamp: str, page: int = 1, page_size: int = 10):
        async with self.session_manager.session() as session:
            # Calculate offset
            offset = (page - 1) * page_size

            total_items_result = await session.execute(
                select(func.count(MinerReceipt.id))
                .where(MinerReceipt.timestamp >= timestamp)
            )
            total_items = total_items_result.scalar()
            total_pages = (total_items + page_size - 1) // page_size

            result = await session.execute(
                select(MinerReceipt)
                .where(MinerReceipt.timestamp >= timestamp)
                .order_by(MinerReceipt.timestamp.asc())
                .limit(page_size)
                .offset(offset)
            )
            receipts = result.scalars().all()

            return {
                "data": receipts,
                "total_pages": total_pages,
                "total_items": total_items
            }

    async def get_last_receipt_timestamp_for_validator_key(self, validator_key: str) -> dict | None:
        async with self.session_manager.session() as session:
            query = select(MinerReceipt).where(MinerReceipt.validator_key == validator_key).order_by(MinerReceipt.timestamp.desc()).limit(1)
            result = await session.execute(query)

            if result is None:
                return None

            return {
                "timestamp": result.timestamp
            }

    async def get_receipt_miner_rank(self, network: str) -> List[ReceiptMinerRank]:
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
                                    timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AND network = :network
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

            result = await session.execute(query, {"network": network}).fetchone()
            result = [ReceiptMinerRank(miner_ratio=row['ratio'], miner_rank=row['rank']) for row in result]

            return result

    async def get_receipts_count_by_networks(self) -> dict:
        async with self.session_manager.session() as session:
            query = text("""
                SELECT 
                    network,
                    COUNT(*) AS count
                FROM 
                    miner_receipts
                WHERE 
                    timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                GROUP BY 
                    network
            """)

            result = await session.execute(query)
            result = result.fetchall()
            return {row[0]: row[1] for row in result}

    async def get_receipt_miner_multiplier(self, network: Optional[str] = None, miner_key: Optional[str] = None) -> List[Dict]:
        async with self.session_manager.session() as session:
            miner_key_filter = "AND miner_receipts.miner_key = :miner_key" if miner_key else ""
            network_filter = "AND miner_receipts.network = :network" if network else ""

            query = text(f"""
                WITH total_receipts AS (
                    SELECT network, COUNT(*) AS total_count
                    FROM miner_receipts
                    WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                    GROUP BY network
                ),
                miner_accepted_counts AS (
                    SELECT 
                        miner_key,
                        network,
                        COUNT(CASE WHEN accepted = True THEN 1 END) AS accepted_true_count
                    FROM 
                        miner_receipts
                    WHERE 
                        timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                        {miner_key_filter}
                        {network_filter}
                    GROUP BY 
                        miner_key, network
                )
                SELECT 
                    mac.miner_key,
                    mac.network,
                    CASE 
                        WHEN tr.total_count = 0 THEN 0
                        ELSE POWER(mac.accepted_true_count::float / tr.total_count, 2)
                    END AS multiplier
                FROM 
                    miner_accepted_counts mac
                JOIN
                    total_receipts tr ON mac.network = tr.network
                ORDER BY multiplier DESC;
            """)

            params = {}
            if miner_key:
                params['miner_key'] = miner_key
            if network:
                params['network'] = network

            result = await session.execute(query, params)
            result = result.fetchall()

            return [{ 'miner_key': row[0], 'network': row[1], 'multiplier': row[2]} for row in result]
