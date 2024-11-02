from typing import Optional, List
from src.subnet.protocol import NETWORK_BITCOIN, MODEL_KIND_FUNDS_FLOW
from src.subnet.validator.validator import Validator
from src.subnet.validator_api.services import FundsFlowQueryApi


class BitcoinFundsFlowQueryApi(FundsFlowQueryApi):
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

        # Corrected Cypher query with value_satoshi and optional matching for coinbase transactions
        query = f"""
            MATCH (t1:Transaction)
            WHERE t1.block_height IN {block_heights}
            OPTIONAL MATCH (a1:Address)-[s1:SENT]->(t1)
            OPTIONAL MATCH (t1)-[s2:SENT]->(a2:Address)
            RETURN a1,s1,t1,s2,a2
        """

        data = await self._execute_query(query)
        return data

    async def get_blocks_around_transaction(self, tx_id: str, left_hops: int, right_hops: int) -> dict:
        """Retrieve the transaction, its vins/vouts, and related paths within the specified hops."""

        if left_hops > 4 or right_hops > 4:
            raise ValueError("Hops cannot exceed 4 in either direction")

        query = f"""
            MATCH path1 = (a0:Address)-[s0:SENT*0..{left_hops}]->(t1:Transaction {{tx_id: '{tx_id}'}})
            MATCH path2 = (t1)-[s1:SENT*0..{right_hops}]->(a1:Address)
            RETURN path1, path2
        """

        data = await self._execute_query(query)
        return data

    async def get_address_transactions(self,
                                       address: str,
                                       start_block_height: Optional[int] = None,
                                       end_block_height: Optional[int] = None,
                                       limit: Optional[int] = 100) -> dict:
        # Start with the original query structure
        query = f"""
            MATCH (a:Address {{address: '{address}'}})
            OPTIONAL MATCH (a)-[s1:SENT]->(t1:Transaction)
        """

        # Add block height condition for t1 if provided
        if start_block_height is not None or end_block_height is not None:
            t1_conditions = []
            if start_block_height is not None:
                t1_conditions.append(f"t1.block_height >= {start_block_height}")
            if end_block_height is not None:
                t1_conditions.append(f"t1.block_height <= {end_block_height}")
            query += f"WHERE {' AND '.join(t1_conditions)}\n"

        # Continue building the query with the rest of the structure
        query += f"""
            OPTIONAL MATCH (t1)-[s2:SENT]->(a2:Address)
            OPTIONAL MATCH (t2:Transaction)-[s4:SENT]->(a)
        """

        # Add block height condition for t2 if provided
        if start_block_height is not None or end_block_height is not None:
            t2_conditions = []
            if start_block_height is not None:
                t2_conditions.append(f"t2.block_height >= {start_block_height}")
            if end_block_height is not None:
                t2_conditions.append(f"t2.block_height <= {end_block_height}")
            query += f"WHERE {' AND '.join(t2_conditions)}\n"

        # Add remaining structure
        query += f"""
            OPTIONAL MATCH (a3:Address)-[s3:SENT]->(t2)
            OPTIONAL MATCH (t2)-[s5:SENT]->(a4:Address)
            WITH a, s1, t1, s2, a2, a3, s3, t2, s4, s5, a4
            WHERE t1 IS NOT NULL OR t2 IS NOT NULL
            RETURN a, s1, t1, s2, a2, a3, s3, t2, s4, s5, a4
            LIMIT {limit}
        """

        # Execute the query
        data = await self._execute_query(query)
        return data

    async def get_funds_flow(self,
                             address: str,
                             direction: str,
                             intermediate_addresses: Optional[List[str]] = None,
                             hops: Optional[int] = 5,
                             start_block_height: Optional[int] = None,
                             end_block_height: Optional[int] = None) -> dict:

        # Start with the base path matching with hops included
        if direction == 'right':
            base_query = f"""
            MATCH path1 = (a1:Address {{address: '{address}'}})
                          -[s1:SENT]->(t1:Transaction)
                          -[s2:SENT*1..{hops}]->(a2:Address)
            """
        elif direction == 'left':
            base_query = f"""
            MATCH path1 = (a1:Address {{address: '{address}'}})
                          <-[s1:SENT]-(t1:Transaction)
                          <-[s2:SENT*1..{hops}]-(a2:Address)
            """
        else:
            raise ValueError("Direction must be either 'left' or 'right'")

        query_elements = [base_query]

        # Add block height filtering if specified
        if start_block_height is not None and end_block_height is not None:
            query_elements.append(f"WHERE t1.block_height IN range({start_block_height}, {end_block_height})")

        # Handle intermediate address filtering if provided
        if intermediate_addresses:
            intermediates_condition = " AND ".join(
                [f"'{addr}' IN [x IN nodes(path1) | x.address]" for addr in intermediate_addresses]
            )
            query_elements.append(f"AND {intermediates_condition}")

        # Return only path1, which contains all relevant information
        query_elements.append("RETURN path1")

        # Assemble the final query string
        final_query = "\n".join(query_elements)

        # Execute the query and transform the results
        data = await self._execute_query(final_query)
        return data
