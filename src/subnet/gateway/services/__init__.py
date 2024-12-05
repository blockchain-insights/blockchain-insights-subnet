class MoneyFlowQueryApi:

    async def get_block(self, block_height: int) -> dict:
        pass

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:
        pass

    async def get_address_transactions(self, address: str) -> dict:
        pass
