import time
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.subnet.validator.database import db_manager
from .. import BaseBalanceSearch
from loguru import logger


class BitcoinBalanceSearch(BaseBalanceSearch):
    def __init__(self):
        pass

    async def execute_query(self, query: str):
        try:
            logger.info(f"Executing SQL query: {query}")
            async with db_manager.session() as session:
                async with session.begin():
                    await session.execute(text("SET TRANSACTION READ ONLY"))
                    result = await session.execute(text(query))
                    rows = result.fetchall()
                    columns = result.keys()
                    results = [dict(zip(columns, row)) for row in rows]
                    return results

        except SQLAlchemyError as e:
            logger.error(f"An error occurred: {str(e)}")
            raise ValueError("Query attempted to modify data, which is not allowed.") from e

    async def solve_challenge(self, block_heights: list[int]):
        start_time = time.time()
        try:
            logger.info(f"Executing balance sum query for block heights: {block_heights}")
            async with db_manager.session() as session:
                query = text("SELECT SUM(d_balance) FROM balance_changes WHERE block = ANY(:block_heights)")
                query = await session.execute(query, {'block_heights': block_heights})
                result = query.scalar()
                if result:
                    sum_d_balance = int(result)
                else:
                    sum_d_balance = 0

                logger.info(f"Balance sum for block heights {block_heights}: {sum_d_balance}")

                return sum_d_balance

        except SQLAlchemyError as e:
            logger.error(f"An error occurred: {str(e)}")
            return None
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Execution time for solve_challenge: {execution_time} seconds")