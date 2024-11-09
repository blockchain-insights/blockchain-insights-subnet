from typing import List, Optional, Dict, Union
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, update, insert, BigInteger, Boolean, UniqueConstraint, Text, select, \
    func, text, Index
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
    request_id = Column(String, nullable=False)
    miner_key = Column(String, nullable=False)
    model_kind = Column(String, nullable=False)
    network = Column(String, nullable=False)

    query_hash = Column(Text, nullable=False)
    response_hash = Column(Text, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('miner_key', 'request_id', name='uq_miner_key_request_id'),

        Index('idx_miner_receipts_miner_key_timestamp',
              'miner_key', 'timestamp', postgresql_using='btree'),

        Index('idx_miner_receipts_timestamp',
              'timestamp', postgresql_using='btree'),

        Index('idx_miner_receipts_validator_key_timestamp',
              'validator_key', 'timestamp', postgresql_using='btree'),

        Index('idx_miner_receipts_network_timestamp',
              'network', 'timestamp', postgresql_using='btree'),
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
                                  timestamp: datetime, response_hash: str):
        async with self.session_manager.session() as session:
            async with session.begin():
                stmt = insert(MinerReceipt).values(
                    request_id=request_id,
                    miner_key=miner_key,
                    model_kind=model_kind,
                    query_hash=query_hash,
                    network=network,
                    timestamp=timestamp,
                    response_hash=response_hash,
                    is_local_receipt=False,
                    validator_key=validator_key
                ).on_conflict_do_nothing(index_elements=['miner_key', 'request_id'])
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
            query = select(MinerReceipt).where(
                MinerReceipt.validator_key == validator_key
            ).order_by(
                MinerReceipt.timestamp.desc()
            ).limit(1)

            result = await session.scalar(query)

            if result is None:
                return None

            return {
                "timestamp": result.timestamp
            }

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
                    SELECT network, miner_key, COUNT(*) AS total_count
                    FROM miner_receipts
                    WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                    {miner_key_filter}
                    {network_filter}
                    GROUP BY network, miner_key
                ),
                max_receipts_per_network AS (
                    SELECT network, MAX(total_count) as max_count
                    FROM total_receipts
                    GROUP BY network
                )
                SELECT 
                    tr.miner_key,
                    tr.network,
                    CASE 
                        WHEN mrn.max_count = 0 THEN 0
                        ELSE (tr.total_count::float / mrn.max_count)
                    END AS multiplier
                FROM 
                    total_receipts tr
                JOIN
                    max_receipts_per_network mrn ON tr.network = mrn.network
                ORDER BY multiplier DESC;
            """)

            params = {}
            if miner_key:
                params['miner_key'] = miner_key
            if network:
                params['network'] = network

            result = await session.execute(query, params)
            result = result.fetchall()

            return [{'miner_key': row[0], 'network': row[1], 'multiplier': row[2]} for row in result]
