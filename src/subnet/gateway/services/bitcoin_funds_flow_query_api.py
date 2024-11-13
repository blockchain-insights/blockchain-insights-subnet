from typing import Optional, List
from src.subnet.protocol import NETWORK_BITCOIN, MODEL_KIND_FUNDS_FLOW
from src.subnet.validator.validator import Validator
from src.subnet.gateway.services import FundsFlowQueryApi


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

    async def get_blocks(self, block_height: int) -> dict:
        if block_height <= 0:
            raise ValueError("Block height must be a positive integer")

        query = """
                MATCH (t1:Transaction {block_height:%d})-[s1:SENT]->(a1:Address)
                OPTIONAL MATCH (t0)-[s0:SENT]->(a0:Address)-[s2:SENT]->(t1)
                OPTIONAL MATCH (t1)-[s3:SENT]->(a2:Address)-[s4:SENT]->(t2)

                WITH 
                    COLLECT(DISTINCT CASE WHEN t0 IS NOT NULL THEN {
                        id: t0.tx_id, type: 'node', label: 'transaction', 
                        balance: t0.out_total_amount/100000000.0, timestamp: t0.timestamp, 
                        block_height: t0.block_height } END) AS transactions_t0,
                    COLLECT(DISTINCT CASE WHEN t1 IS NOT NULL THEN {
                        id: t1.tx_id, type: 'node', label: 'transaction', 
                        balance: t1.out_total_amount/100000000.0, timestamp: t1.timestamp, 
                        block_height: t1.block_height } END) AS transactions_t1,
                    COLLECT(DISTINCT CASE WHEN t2 IS NOT NULL THEN {
                        id: t2.tx_id, type: 'node', label: 'transaction', 
                        balance: t2.out_total_amount/100000000.0, timestamp: t2.timestamp, 
                        block_height: t2.block_height } END) AS transactions_t2,

                    COLLECT(DISTINCT CASE WHEN a0 IS NOT NULL THEN {
                        id: a0.address, type: 'node', label: 'address', address: a0.address } END) AS addresses_a0,
                    COLLECT(DISTINCT CASE WHEN a1 IS NOT NULL THEN {
                        id: a1.address, type: 'node', label: 'address', address: a1.address } END) AS addresses_a1,
                    COLLECT(DISTINCT CASE WHEN a2 IS NOT NULL THEN {
                        id: a2.address, type: 'node', label: 'address', address: a2.address } END) AS addresses_a2,
                    
                    COLLECT(DISTINCT CASE WHEN s0 IS NOT NULL THEN {
                        id: t0.tx_id + '-' + a0.address, type: 'edge', label: toString(s0.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t0.tx_id, to_id: a0.address, satoshi_value: s0.value_satoshi, 
                        btc_value: s0.value_satoshi/100000000.0 } END) AS edges_s0,
                    COLLECT(DISTINCT CASE WHEN s1 IS NOT NULL THEN {
                        id: t1.tx_id + '-' + a1.address, type: 'edge', label: toString(s1.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t1.tx_id, to_id: a1.address, satoshi_value: s1.value_satoshi, 
                        btc_value: s1.value_satoshi/100000000.0 } END) AS edges_s1,
                    COLLECT(DISTINCT CASE WHEN s2 IS NOT NULL THEN {
                        id: a0.address + '-' + t1.tx_id, type: 'edge', label: toString(s2.value_satoshi/100000000.0) + ' BTC', 
                        from_id: a0.address, to_id: t1.tx_id, satoshi_value: s2.value_satoshi, 
                        btc_value: s2.value_satoshi/100000000.0 } END) AS edges_s2,
                    COLLECT(DISTINCT CASE WHEN s3 IS NOT NULL THEN {
                        id: t1.tx_id + '-' + a2.address, type: 'edge', label: toString(s3.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t1.tx_id, to_id: a2.address, satoshi_value: s3.value_satoshi, 
                        btc_value: s3.value_satoshi/100000000.0 } END) AS edges_s3,
                    COLLECT(DISTINCT CASE WHEN s4 IS NOT NULL THEN {
                        id: a2.address + '-' + t2.tx_id, type: 'edge', label: toString(s4.value_satoshi/100000000.0) + ' BTC', 
                        from_id: a2.address, to_id: t2.tx_id, satoshi_value: s4.value_satoshi, 
                        btc_value: s4.value_satoshi/100000000.0 } END) AS edges_s4

                WITH transactions_t0 + transactions_t1 + transactions_t2 
                    + addresses_a0 + addresses_a1 + addresses_a2 
                    + edges_s0 + edges_s1 + edges_s2 + edges_s3 + edges_s4 AS elements
                UNWIND elements AS element
                RETURN DISTINCT element.id AS id,
                       element.type AS type,
                       element.label AS label,
                       element.balance AS balance,
                       element.timestamp AS timestamp,
                       element.block_height AS block_height,
                       element.address AS address,
                       element.from_id AS from_id,
                       element.to_id AS to_id,
                       element.satoshi_value AS satoshi_value,
                       element.btc_value AS btc_value
                """ % block_height

        data = await self._execute_query(query)
        return data if data else []

    async def get_blocks_around_transaction(self, tx_id: str, left_hops: int, right_hops: int) -> dict:
        """Retrieve the transaction, its vins/vouts, and related paths within the specified hops."""

        if left_hops > 4 or right_hops > 4:
            raise ValueError("Hops cannot exceed 4 in either direction")

        query = """
                MATCH (t1:Transaction {tx_id:'%s'})-[s1:SENT]->(a1:Address)
                OPTIONAL MATCH (t0)-[s0:SENT]->(a0:Address)-[s2:SENT]->(t1)
                OPTIONAL MATCH (t1)-[s3:SENT]->(a2:Address)-[s4:SENT]->(t2)

                WITH 
                    COLLECT(DISTINCT CASE WHEN t0 IS NOT NULL THEN {
                        id: t0.tx_id, type: 'node', label: 'transaction', 
                        balance: t0.out_total_amount/100000000.0, timestamp: t0.timestamp, 
                        block_height: t0.block_height } END) AS transactions_t0,
                    COLLECT(DISTINCT CASE WHEN t1 IS NOT NULL THEN {
                        id: t1.tx_id, type: 'node', label: 'transaction', 
                        balance: t1.out_total_amount/100000000.0, timestamp: t1.timestamp, 
                        block_height: t1.block_height } END) AS transactions_t1,
                    COLLECT(DISTINCT CASE WHEN t2 IS NOT NULL THEN {
                        id: t2.tx_id, type: 'node', label: 'transaction', 
                        balance: t2.out_total_amount/100000000.0, timestamp: t2.timestamp, 
                        block_height: t2.block_height } END) AS transactions_t2,

                    COLLECT(DISTINCT CASE WHEN a0 IS NOT NULL THEN {
                        id: a0.address, type: 'node', label: 'address', address: a0.address } END) AS addresses_a0,
                    COLLECT(DISTINCT CASE WHEN a1 IS NOT NULL THEN {
                        id: a1.address, type: 'node', label: 'address', address: a1.address } END) AS addresses_a1,
                    COLLECT(DISTINCT CASE WHEN a2 IS NOT NULL THEN {
                        id: a2.address, type: 'node', label: 'address', address: a2.address } END) AS addresses_a2,

                    COLLECT(DISTINCT CASE WHEN s0 IS NOT NULL THEN {
                        id: t0.tx_id + '-' + a0.address, type: 'edge', label: toString(s0.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t0.tx_id, to_id: a0.address, satoshi_value: s0.value_satoshi, 
                        btc_value: s0.value_satoshi/100000000.0 } END) AS edges_s0,
                    COLLECT(DISTINCT CASE WHEN s1 IS NOT NULL THEN {
                        id: t1.tx_id + '-' + a1.address, type: 'edge', label: toString(s1.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t1.tx_id, to_id: a1.address, satoshi_value: s1.value_satoshi, 
                        btc_value: s1.value_satoshi/100000000.0 } END) AS edges_s1,
                    COLLECT(DISTINCT CASE WHEN s2 IS NOT NULL THEN {
                        id: a0.address + '-' + t1.tx_id, type: 'edge', label: toString(s2.value_satoshi/100000000.0) + ' BTC', 
                        from_id: a0.address, to_id: t1.tx_id, satoshi_value: s2.value_satoshi, 
                        btc_value: s2.value_satoshi/100000000.0 } END) AS edges_s2,
                    COLLECT(DISTINCT CASE WHEN s3 IS NOT NULL THEN {
                        id: t1.tx_id + '-' + a2.address, type: 'edge', label: toString(s3.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t1.tx_id, to_id: a2.address, satoshi_value: s3.value_satoshi, 
                        btc_value: s3.value_satoshi/100000000.0 } END) AS edges_s3,
                    COLLECT(DISTINCT CASE WHEN s4 IS NOT NULL THEN {
                        id: a2.address + '-' + t2.tx_id, type: 'edge', label: toString(s4.value_satoshi/100000000.0) + ' BTC', 
                        from_id: a2.address, to_id: t2.tx_id, satoshi_value: s4.value_satoshi, 
                        btc_value: s4.value_satoshi/100000000.0 } END) AS edges_s4

                WITH transactions_t0 + transactions_t1 + transactions_t2 
                    + addresses_a0 + addresses_a1 + addresses_a2 
                    + edges_s0 + edges_s1 + edges_s2 + edges_s3 + edges_s4 AS elements
                UNWIND elements AS element
                RETURN DISTINCT element.id AS id,
                       element.type AS type,
                       element.label AS label,
                       element.balance AS balance,
                       element.timestamp AS timestamp,
                       element.block_height AS block_height,
                       element.address AS address,
                       element.from_id AS from_id,
                       element.to_id AS to_id,
                       element.satoshi_value AS satoshi_value,
                       element.btc_value AS btc_value
                """ % tx_id

        data = await self._execute_query(query)
        return data

    async def get_address_transactions(self,
                                       address: str,
                                       left_hops: int = 2,
                                       right_hops: int =2,
                                       limit: Optional[int] = 100) -> dict:

        query = f"""
            MATCH (a:Address {{address: '{address}'}})
            MATCH path1 = (a)-[s1:SENT*0..{right_hops}]->(t:Transaction)
            MATCH path2 = (other:Address)-[s2:SENT*0..{left_hops}]->(t2:Transaction)-[s3:SENT]->(a)
            OPTIONAL MATCH path3 = (t)-[s4:SENT*1..{right_hops}]->(downstream:Address)
            WHERE downstream <> a
            OPTIONAL MATCH path4 = (upstream:Address)-[s5:SENT*1..{left_hops}]->(t2)
            WHERE upstream <> a
            RETURN path1, path2, path3, path4
            LIMIT {limit}
        """

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
