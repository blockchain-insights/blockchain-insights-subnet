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

    async def get_block(self, block_height: int) -> dict:
        if block_height <= 0:
            raise ValueError("Block height must be a positive integer")

        query = """
                MATCH (t1:Transaction {block_height:%d})-[s1:SENT]->(a1:Address)
                OPTIONAL MATCH (t0)-[s0:SENT]->(a0:Address)-[s2:SENT]->(t1)
                OPTIONAL MATCH (t1)-[s3:SENT]->(a2:Address)-[s4:SENT]->(t2)

                WITH 
                    COLLECT({
                        id: t1.tx_id,
                        type: 'node',
                        label: 'transaction', 
                        amount: t1.out_total_amount/100000000.0,
                        timestamp: t1.timestamp, 
                        block_height: t1.block_height 
                    } END) AS transactions_t1,
                        
                    COLLECT({
                        id: t1.tx_id + '-' + a1.address,
                        type: 'edge',
                        label: toString(s1.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t1.tx_id,
                        to_id: a1.address,
                        satoshi_value: s1.value_satoshi, 
                        btc_value: 
                        s1.value_satoshi/100000000.0 
                    } END) AS edges_s1,
                                       
                    COLLECT({
                        id: a1.address, 
                        type: 'node', 
                        label: 'address', 
                        address: a1.address 
                    } END) AS addresses_a1,                                       
                                       
                    COLLECT(DISTINCT CASE WHEN t0 IS NOT NULL THEN {
                        id: t0.tx_id, 
                        type: 'node',
                        label: 'transaction', 
                        amount: t0.out_total_amount/100000000.0,
                        timestamp: t0.timestamp, 
                        block_height: t0.block_height 
                    } END) AS transactions_t0,
                    
                    COLLECT(DISTINCT CASE WHEN s0 IS NOT NULL THEN {
                        id: t0.tx_id + '-' + a0.address,
                        type: 'edge', 
                        label: toString(s0.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t0.tx_id, 
                        to_id: a0.address, 
                        satoshi_value: s0.value_satoshi, 
                        btc_value: s0.value_satoshi/100000000.0 
                    } END) AS edges_s0,
                    
                    COLLECT(DISTINCT CASE WHEN a0 IS NOT NULL THEN {
                        id: a0.address, 
                        type: 'node', 
                        label: 'address', 
                        address: a0.address 
                    } END) AS addresses_a0,
                        
                    COLLECT(DISTINCT CASE WHEN s2 IS NOT NULL THEN {
                        id: a0.address + '-' + t1.tx_id, 
                        type: 'edge', 
                        label: toString(s2.value_satoshi/100000000.0) + ' BTC', 
                        from_id: a0.address, 
                        to_id: t1.tx_id, 
                        satoshi_value: s2.value_satoshi, 
                        btc_value: s2.value_satoshi/100000000.0 
                    } END) AS edges_s2,
                        
                    COLLECT(DISTINCT CASE WHEN s3 IS NOT NULL THEN {
                        id: t1.tx_id + '-' + a2.address,
                        type: 'edge',
                        label: toString(s3.value_satoshi/100000000.0) + ' BTC', 
                        from_id: t1.tx_id, 
                        to_id: a2.address, 
                        satoshi_value: s3.value_satoshi, 
                        btc_value: s3.value_satoshi/100000000.0 
                    } END) AS edges_s3,    
                        
                    COLLECT(DISTINCT CASE WHEN a2 IS NOT NULL THEN {
                        id: a2.address, 
                        type: 'node', 
                        label: 'address', 
                        address: a2.address 
                    } END) AS addresses_a2,

                   COLLECT(DISTINCT CASE WHEN s4 IS NOT NULL THEN {
                        id: a2.address + '-' + t2.tx_id, 
                        type: 'edge', 
                        label: toString(s4.value_satoshi/100000000.0) + ' BTC', 
                        from_id: a2.address, 
                        to_id: t2.tx_id, 
                        satoshi_value: s4.value_satoshi, 
                        btc_value: s4.value_satoshi/100000000.0 
                    } END) AS edges_s4
                         
                    COLLECT(DISTINCT CASE WHEN t2 IS NOT NULL THEN {
                        id: t2.tx_id, 
                        type: 'node', 
                        label: 'transaction', 
                        amount: t2.out_total_amount/100000000.0, 
                        timestamp: t2.timestamp, 
                        block_height: t2.block_height 
                    } END) AS transactions_t2,

                WITH transactions_t0 + transactions_t1 + transactions_t2 
                    + addresses_a0 + addresses_a1 + addresses_a2 
                    + edges_s0 + edges_s1 + edges_s2 + edges_s3 + edges_s4 AS elements
                UNWIND elements AS element
                RETURN DISTINCT element.id AS id,
                       element.type AS type,
                       element.label AS label,
                       element.amount AS amount,
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

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:
        """Retrieve the transaction, its vins/vouts, and related paths within the specified hops."""

        query = """
            MATCH (t1:Transaction {tx_id: '%s'})-[s1:SENT]->(a1:Address)
            OPTIONAL MATCH (a0:Address)-[s2:SENT]->(t1)
            OPTIONAL MATCH (t1)-[s3:SENT]->(a2:Address)
            WITH DISTINCT t1, s1, a1, a0, s2, s3, a2
            WITH 
                COLLECT({
                    id: t1.tx_id, 
                    type: 'node', 
                    label: 'transaction', 
                    amount: t1.out_total_amount / 100000000.0, 
                    timestamp: t1.timestamp,
                    block_height: t1.block_height 
                } END) AS transactions_t1,

                COLLECT({
                    id: t1.tx_id + '-' + a1.address,
                    type: 'edge', 
                    label: toString(s1.value_satoshi / 100000000.0) + ' BTC', 
                    from_id: t1.tx_id, 
                    to_id: a1.address, 
                    satoshi_value: s1.value_satoshi, 
                    btc_value: s1.value_satoshi / 100000000.0 
                } END) AS edges_s1,

                COLLECT( {
                    id: a1.address, 
                    type: 'node',
                    label: 'address',
                    address: a1.address 
                } END) AS addresses_a1,

                COLLECT(CASE WHEN a0 IS NOT NULL THEN {
                    id: a0.address, 
                    type: 'node',
                    label: 'address',
                    address: a0.address 
                } END) AS addresses_a0,
                
                COLLECT(CASE WHEN a2 IS NOT NULL THEN {
                    id: a2.address,
                    type: 'node',
                    label: 'address',
                    address: a2.address 
                } END) AS addresses_a2,
                
                COLLECT(CASE WHEN s2 IS NOT NULL THEN {
                    id: a0.address + '-' + t1.tx_id,
                    type: 'edge', 
                    label: toString(s2.value_satoshi / 100000000.0) + ' BTC', 
                    from_id: a0.address,
                    to_id: t1.tx_id, 
                    satoshi_value: s2.value_satoshi, 
                    btc_value: s2.value_satoshi / 100000000.0 
                } END) AS edges_s2,
                
                COLLECT(CASE WHEN s3 IS NOT NULL THEN {
                    id: t1.tx_id + '-' + a2.address,
                    type: 'edge', 
                    label: toString(s3.value_satoshi / 100000000.0) + ' BTC', 
                    from_id: t1.tx_id,
                    to_id: a2.address, 
                    satoshi_value: s3.value_satoshi, 
                    btc_value: s3.value_satoshi / 100000000.0 
                } END) AS edges_s3

            WITH transactions_t1 
                + addresses_a0 + addresses_a1 + addresses_a2 
                + edges_s1 + edges_s2 + edges_s3 AS elements
            UNWIND elements AS element
            RETURN element.id AS id,
                   element.type AS type,
                   element.label AS label,
                   element.amount AS amount,
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

    async def get_address_transactions(self, address: str, limit: Optional[int] = 100) -> dict:

        if not isinstance(address, str) or not address.strip():
            raise ValueError("Address must be a non-empty string")

        query = """
            MATCH (a0:Address {address: '%s'})
            MATCH (a0)<-[s0:SENT]-(t0:Transaction)<-[s3:SENT]-(a3:Address)
            OPTIONAL MATCH (a0)-[s1:SENT]->(t1:Transaction)-[s2:SENT]->(a1:Address)

            WITH DISTINCT
                a0, s0, t0, s3, a3, s1, t1, s2, a1

            WITH 
                COLLECT({
                    id: t1.tx_id,
                    type: 'node',
                    label: 'transaction',
                    amount: t1.out_total_amount/100000000.0,
                    timestamp: t1.timestamp,
                    block_height: t1.block_height
                }) AS out_txs,
                COLLECT(DISTINCT {
                    id: t0.tx_id,
                    type: 'node',
                    label: 'transaction',
                    amount: t0.out_total_amount/100000000.0,
                    timestamp: t0.timestamp,
                    block_height: t0.block_height
                }) AS in_txs,
                COLLECT(DISTINCT {
                    id: a1.address,
                    type: 'node',
                    label: 'address',
                    address: a1.address
                }) AS out_addresses,
                COLLECT(DISTINCT {
                    id: a3.address,
                    type: 'node',
                    label: 'address',
                    address: a3.address
                }) AS in_addresses,
                COLLECT(DISTINCT {
                    id: a0.address,
                    type: 'node',
                    label: 'address',
                    address: a0.address
                })[0] AS center_address,
                COLLECT(DISTINCT {
                    id: t1.tx_id + '-' + a1.address,
                    type: 'edge',
                    label: toString(s2.value_satoshi/100000000.0) + ' BTC',
                    from_id: t1.tx_id,
                    to_id: a1.address,
                    satoshi_value: s2.value_satoshi,
                    btc_value: s2.value_satoshi/100000000.0,
                    timestamp: t1.timestamp
                }) AS out_edges1,
                COLLECT(DISTINCT {
                    id: a0.address + '-' + t1.tx_id,
                    type: 'edge',
                    label: toString(s1.value_satoshi/100000000.0) + ' BTC',
                    from_id: a0.address,
                    to_id: t1.tx_id,
                    satoshi_value: s1.value_satoshi,
                    btc_value: s1.value_satoshi/100000000.0,
                    timestamp: t1.timestamp
                }) AS out_edges2,
                COLLECT(DISTINCT {
                    id: t0.tx_id + '-' + a0.address,
                    type: 'edge',
                    label: toString(s0.value_satoshi/100000000.0) + ' BTC',
                    from_id: t0.tx_id,
                    to_id: a0.address,
                    satoshi_value: s0.value_satoshi,
                    btc_value: s0.value_satoshi/100000000.0,
                    timestamp: t0.timestamp
                }) AS in_edges1,
                COLLECT(DISTINCT {
                    id: a3.address + '-' + t0.tx_id,
                    type: 'edge',
                    label: toString(s3.value_satoshi/100000000.0) + ' BTC',
                    from_id: a3.address,
                    to_id: t0.tx_id,
                    satoshi_value: s3.value_satoshi,
                    btc_value: s3.value_satoshi/100000000.0,
                    timestamp: t0.timestamp
                }) AS in_edges2

            WITH out_txs + in_txs + [center_address] + out_addresses + in_addresses + 
                 out_edges1 + out_edges2 + in_edges1 + in_edges2 AS elements

            UNWIND elements AS element
            WITH element
            WHERE element.id IS NOT NULL

            RETURN DISTINCT 
                element.id AS id,
                element.type AS type,
                element.label AS label,
                element.amount AS amount,
                element.timestamp AS timestamp,
                element.block_height AS block_height,
                element.address AS address,
                element.from_id AS from_id,
                element.to_id AS to_id,
                element.satoshi_value AS satoshi_value,
                element.btc_value AS btc_value
            ORDER BY element.timestamp DESC
        """ % address

        data = await self._execute_query(query)
        return data if data else []
