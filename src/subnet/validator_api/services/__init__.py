from typing import Optional, List


class FundsFlowQueryApi:

    async def get_block(self, block_height: int) -> dict:


        # i need to call validator.query_funds_flow(network, cypher_query)


        pass

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:
        pass

    async def get_address_transactions(self,
                                       address: str,
                                       start_block_height: Optional[int],
                                       end_block_height: Optional[int]) -> dict:
        pass

    async def get_funds_flow(self,
                             address: str,
                             intermediate_addresses: Optional[List[str]],
                             hops: Optional[int],
                             start_block_height: Optional[int],
                             end_block_height: Optional[int]) -> dict:
        pass