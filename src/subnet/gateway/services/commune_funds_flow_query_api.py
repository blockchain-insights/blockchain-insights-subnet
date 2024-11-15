from src.subnet.protocol import NETWORK_COMMUNE, MODEL_KIND_FUNDS_FLOW
from src.subnet.validator.validator import Validator
from src.subnet.gateway.services import FundsFlowQueryApi


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

    async def get_block(self, block_height: int) -> dict:
        if block_height <= 0:
            raise ValueError("Block height must be a positive integer")

        query = """
            MATCH (a0:Address)-[t:TRANSACTION {block_height: %d}]->(a1:Address)
            WITH DISTINCT a0, a1, t
            WITH 
                COLLECT({
                    id: a0.address,
                    type: 'node',
                    label: 'address',
                    address: a0.address
                }) AS source_addresses,
                
                COLLECT({
                    id: a1.address,
                    type: 'node',
                    label: 'address',
                    address: a1.address
                }) AS target_addresses,
                 
                COLLECT({
                    id: t.id,
                    type: 'edge',
                    block_height: t.block_height,
                    transaction_type: t.type,
                    timestamp: toString(t.timestamp),
                    label: toString(t.amount/1000000000) + ' COMAI',
                    from_id: a0.address,
                    to_id: a1.address,
                    amount: toFloat(t.amount/1000000000)
                }) AS edges
            
            WITH source_addresses + target_addresses + edges AS elements
            UNWIND elements AS element
            RETURN 
                element.id AS id,
                element.type AS type,
                element.label AS label,
                element.amount AS amount,
                element.timestamp AS timestamp,
                element.block_height AS block_height,
                element.transaction_type as transaction_type,
                element.address AS address,
                element.from_id AS from_id,
                element.to_id AS to_id

        """ % block_height

        data = await self._execute_query(query)
        return data

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:

        query = """
            MATCH (a0:Address)-[t:TRANSACTION {id: '%s'}]->(a1:Address)
            WITH DISTINCT a0, a1, t
            WITH 
                COLLECT({
                    id: a0.address,
                    type: 'node',
                    label: 'address',
                    address: a0.address
                }) AS source_addresses,
                
                COLLECT({
                    id: a1.address,
                    type: 'node',
                    label: 'address',
                    address: a1.address
                }) AS target_addresses,
                 
                COLLECT({
                    id: t.id,
                    type: 'edge',
                    block_height: t.block_height,
                    transaction_type: t.type,
                    timestamp: toString(t.timestamp),
                    label: toString(t.amount/1000000000) + ' COMAI',
                    from_id: a0.address,
                    to_id: a1.address,
                    amount: toFloat(t.amount/1000000000)
                }) AS edges
            
            WITH source_addresses + target_addresses + edges AS elements
            UNWIND elements AS element
            RETURN 
                element.id AS id,
                element.type AS type,
                element.label AS label,
                element.amount AS amount,
                element.timestamp AS timestamp,
                element.block_height AS block_height,
                element.transaction_type as transaction_type,
                element.address AS address,
                element.from_id AS from_id,
                element.to_id AS to_id
        """ % tx_id

        data = await self._execute_query(query)
        return data

    async def get_address_transactions(self, address: str) -> dict:
        """
        Retrieve outgoing and incoming transactions for a given address,
        filtered by block height if specified.
        """

        # Start building the query with outgoing and incoming transactions
        query = """
            MATCH (a:Address {address: '%s'})
            OPTIONAL MATCH (a)-[t1:TRANSACTION]->(a2:Address)
            OPTIONAL MATCH (a3:Address)-[t2:TRANSACTION]->(a)
            WITH DISTINCT a, t1, a2, a3, t2
            WITH 
                COLLECT({
                    id: a.address,
                    type: 'node',
                    label: 'address',
                    address: a.address
                }) AS center_address,
                
                COLLECT(CASE WHEN t1 IS NOT NULL THEN {
                    id: t1.id,
                    type: 'edge',
                    block_height: t1.block_height,
                    transaction_type: t1.type,
                    timestamp: toString(t1.timestamp),
                    label: toString(t1.amount/1000000000) + ' COMAI',
                    from_id: a.address,
                    to_id: a2.address,
                    amount: toFloat(t1.amount/1000000000)
                } END) AS edges_t1,
                
                COLLECT(CASE WHEN a2 IS NOT NULL THEN {
                    id: a2.address,
                    type: 'node',
                    label: 'address',
                    address: a2.address
                } END) AS right_address,
                
                COLLECT(CASE WHEN a3 IS NOT NULL THEN {
                    id: a3.address,
                    type: 'node',
                    label: 'address',
                    address: a3.address
                } END) AS left_address,
            
                COLLECT(CASE WHEN t2 IS NOT NULL THEN {
                    id: t2.id,
                    type: 'edge',
                    block_height: t2.block_height,
                    transaction_type: t2.type,
                    timestamp: toString(t2.timestamp),
                    label: toString(t2.amount/1000000000) + ' COMAI',
                    from_id: a3.address,
                    to_id: a.address,
                    amount: toFloat(t2.amount/1000000000)
                } END) AS edges_t2
            
            WITH center_address + edges_t1 + right_address + left_address + edges_t2 AS elements
            UNWIND elements AS element
            RETURN 
                element.id AS id,
                element.type AS type,
                element.label AS label,
                element.amount AS amount,
                element.timestamp AS timestamp,
                element.block_height AS block_height,
                element.transaction_type as transaction_type,
                element.address AS address,
                element.from_id AS from_id,
                element.to_id AS to_id
        """ % address

        data = await self._execute_query(query)
        return data
