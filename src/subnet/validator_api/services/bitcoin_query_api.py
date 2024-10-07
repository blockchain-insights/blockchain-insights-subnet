from typing import Optional, List
from src.subnet.protocol import NETWORK_BITCOIN, MODEL_KIND_FUNDS_FLOW, MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator.validator import Validator
from src.subnet.validator_api.services import QueryApi


class BitcoinQueryApi(QueryApi):
    def __init__(self, validator: Validator):
        super().__init__()
        self.validator = validator

    async def _execute_query(self, query: str, model_kind=MODEL_KIND_FUNDS_FLOW) -> dict:
        try:
            data = await self.validator.query_miner(NETWORK_BITCOIN, model_kind, query, miner_key=None)
            return data
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    async def get_blocks(self, block_heights: List[int]) -> dict:
        # Ensure that the array has no more than 10 block heights
        if len(block_heights) > 10:
            raise ValueError("Cannot query more than 10 blocks at once")

        # Form a Cypher query that uses the array of block heights
        query = f"""
            MATCH (t1:Transaction)
            WHERE t1.block_height IN {block_heights}
            OPTIONAL MATCH (t1)-[s1:SENT]->(a1:Address)
            OPTIONAL MATCH (a2:Address)-[s2:SENT]->(t1)
            RETURN t1, s1, a1, s2, a2
        """

        # Execute the query and fetch the data
        data = await self._execute_query(query)

        # Transform data if necessary
        transformed_data = data  # TODO: Add any data transformation here if needed

        return transformed_data

    async def get_blocks_around_transaction(self, tx_id: str, radius: int) -> dict:
        # Ensure the radius is within the allowed limit (R <= 10)
        if radius > 10:
            raise ValueError("Radius cannot be more than 10 blocks")

        query = f"""
            MATCH (t1:Transaction {{tx_id: '{tx_id}'}})
            WITH t1.block_height AS target_block_height
            UNWIND range(target_block_height - {radius}, target_block_height + {radius}) AS block_height
            MATCH (t:Transaction {{block_height: block_height}})-[s1:SENT]->(a1:Address)
            OPTIONAL MATCH (t)-[s2:SENT]->(a2:Address)
            RETURN t AS t1, t.block_height AS block_height, a1, s1, a2, s2
            ORDER BY t.block_height
        """

        data = await self._execute_query(query)

        # Optionally transform data if necessary
        transformed_data = data  # Placeholder for any transformation logic
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

        query = """
            SELECT
                bc.address,
                bc.block,
                bc.d_balance,
                bc.block_timestamp,
                b.timestamp
            FROM
                balance_changes bc
            JOIN
                blocks b ON bc.block = b.block_height
            WHERE
                1=1
        """

        if addresses:
            formatted_addresses = ', '.join(f"'{address}'" for address in addresses)
            query += f" AND bc.address IN ({formatted_addresses})"

        if min_amount is not None:
            query += f" AND bc.d_balance >= {min_amount}"

        if max_amount is not None:
            query += f" AND bc.d_balance <= {max_amount}"

        if start_block_height is not None:
            query += f" AND b.block_height >= {start_block_height}"

        if end_block_height is not None:
            query += f" AND b.block_height <= {end_block_height}"

        query += " ORDER BY bc.block_timestamp;"

        data = await self._execute_query(query, model_kind=MODEL_KIND_BALANCE_TRACKING)
        transformed_data = data  # TODO: Transform the data if necessary

        return transformed_data

    async def get_balance_tracking_timestamp(self,
                                             start_block_height: Optional[int],
                                             end_block_height: Optional[int]) -> dict:
        query = """
            SELECT
                block_height,
                timestamp
            FROM
                blocks
            WHERE
                1=1
        """

        if start_block_height is not None:
            query += f" AND block_height >= {start_block_height}"

        if end_block_height is not None:
            query += f" AND block_height <= {end_block_height}"

        query += " ORDER BY timestamp;"

        data = await self._execute_query(query, model_kind=MODEL_KIND_BALANCE_TRACKING)
        transformed_data = data  # TODO: Transform the data if necessary
        return transformed_data
