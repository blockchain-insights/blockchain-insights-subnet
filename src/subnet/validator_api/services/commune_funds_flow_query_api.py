from typing import Optional, List
from src.subnet.protocol import NETWORK_COMMUNE, MODEL_KIND_FUNDS_FLOW
from src.subnet.validator.validator import Validator
from src.subnet.validator_api.services import FundsFlowQueryApi


class CommuneFundsFlowQueryApi(FundsFlowQueryApi):
    def __init__(self, validator: Validator):
        super().__init__()
        self.validator = validator

    async def _execute_query(self, query: str, model_kind=MODEL_KIND_FUNDS_FLOW) -> dict:
        try:
            data = await self.validator.query_miner(NETWORK_COMMUNE, model_kind, query, miner_key=None)
            return data
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    async def get_blocks(self, block_heights: List[int]) -> dict:
        # Ensure that the array has no more than 10 block heights
        if len(block_heights) > 10:
            raise ValueError("Cannot query more than 10 blocks at once")

        # Corrected Cypher query with value_satoshi and optional matching for coinbase transactions
        query = f"""
            MATCH (a1:Address)-[t:TRANSACTION]->(a2:Address)
            WHERE t.block_height IN {block_heights}
            RETURN a1, t, a2
        """

        # Execute the query and fetch the data
        data = await self._execute_query(query)

        # Transform data if necessary
        transformed_data = data  # TODO: Add any data transformation here if needed

        return transformed_data

    async def get_blocks_around_transaction(self, tx_id: str, left_hops: int, right_hops: int) -> dict:
        # Ensure hops are within the allowed limits
        if left_hops > 4 or right_hops > 4:
            raise ValueError("Hops cannot exceed 4 in either direction")

        # Construct the Cypher query to traverse the graph
        query = f"""
            MATCH path1 = (a0:Address)-[:TRANSACTION*0..{left_hops}]->
                          (a1:Address)-[t:TRANSACTION {{id: '{tx_id}'}}]->(a2:Address)
            OPTIONAL MATCH path2 = (a2)-[:TRANSACTION*0..{right_hops}]->(a3:Address)
            RETURN path1, path2
        """

        # Execute the query and return the results
        data = await self._execute_query(query)
        return data

    async def get_address_transactions(
            self,
            address: str,
            start_block_height: Optional[int] = None,
            end_block_height: Optional[int] = None,
            limit: Optional[int] = 100
    ) -> dict:
        """
        Retrieve outgoing and incoming transactions for a given address,
        filtered by block height if specified.
        """

        # Start building the query with outgoing and incoming transactions
        query = f"""
            MATCH (a:Address {{address: '{address}'}})
            OPTIONAL MATCH (a)-[t1:TRANSACTION]->(a2:Address)  // Outgoing transactions
            OPTIONAL MATCH (a3:Address)-[t2:TRANSACTION]->(a)  // Incoming transactions
        """

        # Add block height filtering with correct logic
        conditions = []
        if start_block_height is not None and end_block_height is not None:
            conditions.append(
                f"((t1.block_height >= {start_block_height} AND t1.block_height <= {end_block_height}) "
                f"OR (t2.block_height >= {start_block_height} AND t2.block_height <= {end_block_height}))"
            )
        elif start_block_height is not None:
            conditions.append(f"(t1.block_height >= {start_block_height} OR t2.block_height >= {start_block_height})")
        elif end_block_height is not None:
            conditions.append(f"(t1.block_height <= {end_block_height} OR t2.block_height <= {end_block_height})")

        if conditions:
            query += f"WHERE {' AND '.join(conditions)}\n"

        # Complete the query with result aggregation and limit
        query += f"""
            WITH a, t1, a2, t2, a3
            WHERE t1 IS NOT NULL OR t2 IS NOT NULL
            RETURN a, t1, a2, t2, a3
            LIMIT {limit}
        """

        # Execute the query and get the result
        data = await self._execute_query(query)

        # Transform the result if needed
        transformed_data = data

        return transformed_data

    async def get_funds_flow(
            self,
            address: str,
            direction: str,
            intermediate_addresses: Optional[List[str]] = None,
            hops: Optional[int] = 5,
            start_block_height: Optional[int] = None,
            end_block_height: Optional[int] = None
    ) -> dict:
        """Retrieve funds flow for the specified address, direction, and hops."""

        # Construct the base query based on the direction
        if direction == 'right':
            # Outgoing funds flow
            base_query = f"""
            MATCH path1 = (a1:Address {{address: '{address}'}})
                          -[:TRANSACTION*1..{hops}]->(a2:Address)
            """
        elif direction == 'left':
            # Incoming funds flow
            base_query = f"""
            MATCH path1 = (a2:Address)
                          -[:TRANSACTION*1..{hops}]->(a1:Address {{address: '{address}'}})
            """
        else:
            raise ValueError("Direction must be either 'left' or 'right'")

        query_elements = [base_query]

        # Add block height filtering if specified
        if start_block_height is not None or end_block_height is not None:
            block_conditions = []
            if start_block_height is not None:
                block_conditions.append(f"r.block_height >= {start_block_height}")
            if end_block_height is not None:
                block_conditions.append(f"r.block_height <= {end_block_height}")
            query_elements.append(f"WHERE {' AND '.join(block_conditions)}")

        # Add filtering for intermediate addresses if provided
        if intermediate_addresses:
            intermediates_condition = " AND ".join(
                [f"'{addr}' IN [x IN nodes(path1) | x.address]" for addr in intermediate_addresses]
            )
            query_elements.append(f"AND {intermediates_condition}")

        # Complete the query with the RETURN statement
        query_elements.append("RETURN path1")

        # Assemble the final query
        final_query = "\n".join(query_elements)

        # Execute the query and transform the results
        data = await self._execute_query(final_query)
        transformed_data = data  # Apply any necessary transformations

        return transformed_data
