import time
from loguru import logger
from src.subnet.miner.blockchain import GraphSearch


class UtxoGraphSearch(GraphSearch):

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
