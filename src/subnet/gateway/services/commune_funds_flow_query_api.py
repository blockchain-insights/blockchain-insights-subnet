from typing import Optional
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
            WITH 
                COLLECT(DISTINCT {
                    id: a0.address,
                    type: 'node',
                    label: 'address',
                    address: a0.address
                }) AS source_addresses,
                
                COLLECT(DISTINCT {
                    id: a1.address,
                    type: 'node',
                    label: 'address',
                    address: a1.address
                }) AS target_addresses,
                
                COLLECT(DISTINCT {
                    id: t.tx_id,
                    type: 'node',
                    label: 'transaction',
                    balance: t.amount,
                    timestamp: t.timestamp,
                    block_height: t.block_height
                }) AS transactions,
                
                COLLECT(DISTINCT {
                    id: t.tx_id + '-' + a1.address,
                    type: 'edge',
                    label: toString(t.amount) + ' COMAI',
                    from_id: a0.address,
                    to_id: a1.address,
                    amount: t.amount,
                }) AS edges
            
            WITH source_addresses + target_addresses + transactions + edges AS elements
            UNWIND elements AS element
            RETURN DISTINCT 
                element.id AS id,
                element.type AS type,
                element.label AS label,
                element.balance AS balance,
                element.timestamp AS timestamp,
                element.block_height AS block_height,
                element.address AS address,
                element.from_id AS from_id,
                element.to_id AS to_id,
                element.balance AS balance
        """ % block_height

        data = await self._execute_query(query)
        return data

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:

        query = """
            MATCH (a0:Address)-[t:TRANSACTION {id: '%s'}]->(a1:Address)
                        WITH 
                COLLECT(DISTINCT {
                    id: a0.address,
                    type: 'node',
                    label: 'address',
                    address: a0.address
                }) AS source_addresses,
                
                COLLECT(DISTINCT {
                    id: a1.address,
                    type: 'node',
                    label: 'address',
                    address: a1.address
                }) AS target_addresses,
                
                COLLECT(DISTINCT {
                    id: t.tx_id,
                    type: 'node',
                    label: 'transaction',
                    balance: t.amount,
                    timestamp: t.timestamp,
                    block_height: t.block_height
                }) AS transactions,
                
                COLLECT(DISTINCT {
                    id: t.tx_id + '-' + a1.address,
                    type: 'edge',
                    label: toString(t.amount) + ' COMAI',
                    from_id: a0.address,
                    to_id: a1.address,
                    amount: t.amount,
                }) AS edges
            
            WITH source_addresses + target_addresses + transactions + edges AS elements
            UNWIND elements AS element
            RETURN DISTINCT 
                element.id AS id,
                element.type AS type,
                element.label AS label,
                element.balance AS balance,
                element.timestamp AS timestamp,
                element.block_height AS block_height,
                element.address AS address,
                element.from_id AS from_id,
                element.to_id AS to_id,
                element.balance AS balance
        """ % tx_id

        data = await self._execute_query(query)
        return data

    async def get_address_transactions(self, address: str) -> dict:
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

        data = await self._execute_query(query)
        return data
