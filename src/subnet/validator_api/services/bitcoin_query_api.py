from typing import Optional
from src.subnet.protocol import NETWORK_BITCOIN, MODEL_TYPE_FUNDS_FLOW
from src.subnet.validator.validator import Validator
from src.subnet.validator_api.services import QueryApi


class BitcoinQueryApi(QueryApi):
    def __init__(self, validator: Validator):
        super().__init__()
        self.validator = validator

    async def _execute_query(self, query: str) -> dict:
        try:
            data = await self.validator.query_miner(NETWORK_BITCOIN, MODEL_TYPE_FUNDS_FLOW, query, miner_key=None)
            return data
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    async def get_block(self, block_height: int) -> dict:
        query = f"""
            MATCH (t1:Transaction)
            WHERE t1.block_height IN [{block_height - 1}, {block_height}, {block_height + 1}]
            OPTIONAL MATCH (t1)-[s1:SENT]->(a1:Address)
            OPTIONAL MATCH (a2:Address)-[s2:SENT]->(t1)
            RETURN t1, s1, a1, s2, a2
        """

        data = await self._execute_query(query)
        transformed_data = data  # TODO: Transform the data if necessary
        return transformed_data

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:
        query = f"""MATCH (t1:Transaction {{tx_id: '{tx_id}' }})
                    OPTIONAL MATCH (t1)-[s1:SENT]->(a1:Address)
                    OPTIONAL MATCH (a2:Address)-[s2:SENT]->(t1)
                    RETURN t1, s1, a1, s2, a2
                """

        data = await self._execute_query(query)
        transformed_data = data  # TODO: Transform data here
        return transformed_data

    async def get_address_transactions(self,
                                       address: str,
                                       start_block_height: Optional[int],
                                       end_block_height: Optional[int],
                                       limit: Optional[int] = 100) -> dict:

        query = f"""
            MATCH (a1:Address {{address: '{address}'}})-[:SENT]-(t1:Transaction)
            OPTIONAL MATCH (t1)-[s2:SENT]->(a2:Address)
            OPTIONAL MATCH (a1)-[s1:SENT]->(t1)
        """

        where_clauses = []
        if start_block_height is not None:
            where_clauses.append(f"t1.block_height >= {start_block_height}")
        if end_block_height is not None:
            where_clauses.append(f"t1.block_height <= {end_block_height}")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += f" RETURN t1, s1, a1, s2, a2 LIMIT {limit}"

        data = await self._execute_query(query)
        transformed_data = data  # TODO: Transform the data if necessary

        return transformed_data

    async def get_funds_flow(self,
                             address: str,
                             intermediate_addresses: Optional[list[str]],
                             hops: Optional[int],
                             start_block_height: Optional[int],
                             end_block_height: Optional[int]) -> dict:

        query_elements = []
        if intermediate_addresses:
            query_elements.append(f"WITH {intermediate_addresses} AS intermediates")

        base_query = f"MATCH (a0:Address {{address: '{address}'}})<-[:SENT]-(t0:Transaction)-[s0:SENT]->(a1:Address)"
        query_elements.append(base_query)

        where_clauses = []
        if start_block_height is not None:
            where_clauses.append(f"t0.block_height >= {start_block_height}")
        if end_block_height is not None:
            where_clauses.append(f"t0.block_height <= {end_block_height}")

        if where_clauses:
            query_elements.append(f"WHERE {' AND '.join(where_clauses)}")

        if intermediate_addresses:
            query_elements.append(f"WHERE a1.address = intermediates[0]")
            query_elements.append(f"""
                WITH a0, t0, s0, a1, intermediates
                UNWIND RANGE(1, SIZE(intermediates)-1) AS idx
                MATCH (a{{idx-1}}:Address {{address: intermediates[idx-1]}})-[s{{idx}}:SENT]->(a{{idx}}:Address {{address: intermediates[idx]}})
            """)

        if hops is not None:
            query_elements.append(f"MATCH path = (a1)-[s1:SENT*1..{hops}]->(an:Address)")
        else:
            query_elements.append(f"MATCH path = (a1)-[s1:SENT*1..5]->(an:Address)")

        query_elements.append(f"RETURN a0, t0, s0, a1, path")
        final_query = "\n".join(query_elements)

        data = await self._execute_query(final_query)
        transformed_data = data  # TODO: Transform the data if necessary

        return transformed_data

    async def get_balance_tracking(self,
                                   addresses: Optional[list[str]],
                                   min_amount: Optional[int],
                                   max_amount: Optional[int],
                                   start_block_height: Optional[int],
                                   end_block_height: Optional[int]) -> dict:
        """
        WITH ['INTERMEDIATE_ADDRESS_1', 'INTERMEDIATE_ADDRESS_2', 'INTERMEDIATE_ADDRESS_3'] AS intermediates
        MATCH (start:Address {address: '1EkKwjuzYNk6YCDiMhSXjA7BLcgQp9GyCu'})<-[:SENT]-(t:Transaction)-[r:SENT]->(a:Address)
        WHERE a.address = intermediates[0] // Ensuring first intermediate is matched
        WITH start, t, r, a, intermediates
        UNWIND RANGE(1, SIZE(intermediates)-1) AS idx
        MATCH (prev:Address {address: intermediates[idx-1]})-[r2:SENT]->(next:Address {address: intermediates[idx]})
        WITH start, t, r, prev, next, intermediates
        MATCH path = (next)-[r3:SENT*1..5]->(final:Address) // Continue after final intermediate
        RETURN start, t, r, prev, next, path
        """
        pass

    async def get_balance_tracking_timestamp(self,
                                             start_block_height: Optional[int],
                                             end_block_height: Optional[int]) -> dict:
            pass