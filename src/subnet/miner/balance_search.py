from src.subnet.validator.database import db_manager
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger


class BalanceSearch:

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