from datetime import datetime
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

        # Corrected Cypher query with value_satoshi and optional matching for coinbase transactions
        query = f"""
            MATCH (t1:Transaction)
            WHERE t1.block_height IN {block_heights}
            OPTIONAL MATCH (a1:Address)-[s1:SENT]->(t1)
            OPTIONAL MATCH (t1)-[s2:SENT]->(a2:Address)
            RETURN a1,s1,t1,s2,a2
        """

        # Execute the query and fetch the data
        data = await self._execute_query(query)

        # Transform data if necessary
        transformed_data = data  # TODO: Add any data transformation here if needed

        return transformed_data

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

        # Optional: Transform the data if needed
        transformed_data = data

        return transformed_data

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
        transformed_data = data  # Apply necessary transformations

        return transformed_data


    async def get_balance_tracking(self,
                                   addresses: Optional[list[str]] = None,
                                   min_amount: Optional[int] = None,
                                   max_amount: Optional[int] = None,
                                   start_block_height: Optional[int] = None,
                                   end_block_height: Optional[int] = None,
                                   start_timestamp: Optional[int] = None,
                                   end_timestamp: Optional[int] = None) -> dict:
        """
        Get balance tracking data filtered by addresses, amount range, block range, and timestamp range.

        Parameters:
        - addresses: List of addresses to filter (optional)
        - min_amount: Minimum balance amount to filter (optional)
        - max_amount: Maximum balance amount to filter (optional)
        - start_block_height: Start block height to filter (optional)
        - end_block_height: End block height to filter (optional)
        - start_timestamp: Start timestamp to filter (optional)
        - end_timestamp: End timestamp to filter (optional)

        Returns:
        - A dictionary with the results of the balance tracking query
        """

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

        # Filter by addresses if provided
        if addresses:
            formatted_addresses = ', '.join(f"'{address}'" for address in addresses)
            query += f" AND bc.address IN ({formatted_addresses})"

        # Filter by balance amount range if provided
        if min_amount is not None:
            query += f" AND bc.d_balance >= {min_amount}"
        if max_amount is not None:
            query += f" AND bc.d_balance <= {max_amount}"

        # Filter by block height range if provided
        if start_block_height is not None:
            query += f" AND b.block_height >= {start_block_height}"
        if end_block_height is not None:
            query += f" AND b.block_height <= {end_block_height}"

        # Filter by timestamp range if provided
        if start_timestamp is not None:
            query += f" AND b.timestamp >= {start_timestamp}"
        if end_timestamp is not None:
            query += f" AND b.timestamp <= {end_timestamp}"

        # Finalize the query with ordering
        query += " ORDER BY bc.block_timestamp;"

        # Execute the query and retrieve data
        data = await self._execute_query(query, model_kind=MODEL_KIND_BALANCE_TRACKING)

        # Transform the data if needed
        transformed_data = data  # TODO: Apply transformation logic if required

        return transformed_data

    async def get_balance_tracking_timestamp(self,
                                             start_date: Optional[str] = None,
                                             end_date: Optional[str] = None) -> dict:
        # Base query to fetch block height and timestamp
        query = """
            SELECT
                block_height,
                timestamp
            FROM
                blocks
        """

        # Initialize conditions list
        conditions = []

        # Process start and end dates to filter the query
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                conditions.append(f"timestamp >= '{start_datetime}'")
            except ValueError:
                raise ValueError("Invalid start_date format. Use YYYY-MM-DD.")

        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                conditions.append(f"timestamp <= '{end_datetime}'")
            except ValueError:
                raise ValueError("Invalid end_date format. Use YYYY-MM-DD.")

        # If there are any conditions, append them to the query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Order the result by timestamp
        query += " ORDER BY timestamp;"

        # Execute the query and return the result
        data = await self._execute_query(query, model_kind=MODEL_KIND_BALANCE_TRACKING)

        # Directly return the data as JSON (no transformation required for now)
        return data