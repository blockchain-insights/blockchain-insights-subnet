import time

from neo4j import GraphDatabase
from loguru import logger

from src.subnet.miner._config import MinerSettings
from src.subnet.miner.blockchain import BaseGraphSearch
from src.subnet.miner.blockchain.bitcoin.query_builder import QueryBuilder
from src.subnet.protocol.llm_engine import Query


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

    def execute_predefined_query(self, query: Query):
        cypher_query = QueryBuilder.build_query(query)
        logger.info(f"Executing cypher query: {cypher_query}")
        result = self._execute_cypher_query(cypher_query)
        return result

    def execute_query(self, query: str):
        logger.info(f"Executing cypher query: {query}")
        result = self._execute_cypher_query(query)
        return result

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

    def _execute_cypher_query(self, cypher_query: str):
        with self.driver.session() as session:
            result = session.run(cypher_query)
            if not result:
                return None

            # TODO: remove hardcodes
            results_data = []
            for record in result:
                # Extract nodes and relationships from the record
                a1 = record['a1']
                t1 = record['t1']
                a2 = record['a2']
                s1 = record['s1']
                s2 = record['s2']

                results_data.append({
                    'a1': a1,
                    't1': t1,
                    'a2': a2,
                    's1': dict(s1),
                    's2': dict(s2)
                })

            return results_data
