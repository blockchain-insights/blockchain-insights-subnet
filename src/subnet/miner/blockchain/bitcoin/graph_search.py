import time

from neo4j import GraphDatabase, READ_ACCESS
from neo4j.exceptions import Neo4jError

from src.subnet.miner._config import MinerSettings
from src.subnet.miner.blockchain import BaseGraphSearch
from loguru import logger


class BitcoinGraphSearch(BaseGraphSearch):
    def __init__(self, settings: MinerSettings):
        logger.info(f'Here is loaded configs {settings.GRAPH_DATABASE_URL}')
        self.driver = GraphDatabase.driver(
            settings.GRAPH_DATABASE_URL,
            auth=(settings.GRAPH_DATABASE_USER, settings.GRAPH_DATABASE_PASSWORD),
            connection_timeout=60,
            max_connection_lifetime=60,
            max_connection_pool_size=128,
            encrypted=False,
        )

    def close(self):
        self.driver.close()

    def solve_challenge(self, in_total_amount: int, out_total_amount: int, tx_id_last_6_chars: str) -> str | None:
        start_time = time.time()
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (t:Transaction {out_total_amount: $out_total_amount})
                    WHERE t.in_total_amount = $in_total_amount AND t.tx_id ENDS WITH $tx_id_last_6_chars
                    RETURN t.tx_id
                    LIMIT 1;
                    """,
                    in_total_amount=in_total_amount,
                    out_total_amount=out_total_amount,
                    tx_id_last_6_chars=tx_id_last_6_chars
                )
                single_result = result.single()
                if single_result is None or single_result[0] is None:
                    return None
                return single_result[0]
        except Exception as e:
            return None
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Execution time for solve_challenge: {execution_time} seconds")

    def execute_query(self, query: str):
        with self.driver.session(default_access_mode=READ_ACCESS) as session:
            try:
                result = session.run(query)
                if not result:
                    return None

                result_data = result.data()
                results_data = []

                for record in result_data:
                    processed_record = {}
                    for key, value in record.items():
                        if hasattr(value, 'items'):
                            processed_record[key] = dict(value)
                        else:
                            processed_record[key] = value
                    results_data.append(processed_record)
                return results_data

            except Neo4jError as e:
                raise ValueError("Query attempted to modify data, which is not allowed.") from e

