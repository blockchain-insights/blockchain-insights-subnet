from typing import Optional

from src.subnet.validator_api.services import QueryApi


class BitcoinQueryApi(QueryApi):

    async def get_block(self, block_height: int) -> dict:
        """
        MATCH (t:Transaction {block_height: 108320})
        OPTIONAL MATCH (t)-[outS:SENT]->(outAddr:Address)
        OPTIONAL MATCH (inAddr:Address)-[inS:SENT]->(t)
        RETURN t, outS, outAddr, inS, inAddr
        """
        pass

    async def get_transaction_by_tx_id(self, tx_id: str) -> dict:
        """
        MATCH (t:Transaction {tx_id: '12bfb9d98ad58af5423423af525239d25eb11458d20d4c5500808ee60b2bf3b5' })
        OPTIONAL MATCH (t)-[outS:SENT]->(outAddr:Address)
        OPTIONAL MATCH (inAddr:Address)-[inS:SENT]->(t)
        RETURN t, outS, outAddr, inS, inAddr
        """
        pass

    async def get_address_transactions(self,
                                       address: str,
                                       start_block_height: Optional[int],
                                       end_block_height: Optional[int]) -> dict:

        """
        MATCH (addr:Address {address: '1EkKwjuzYNk6YCDiMhSXjA7BLcgQp9GyCu'})-[:SENT]-(t:Transaction)
        OPTIONAL MATCH (t)-[outS:SENT]->(outAddr:Address)
        OPTIONAL MATCH (inAddr:Address)-[inS:SENT]->(t)
        RETURN t, outS, outAddr, inS, inAddr
        """
        pass

    async def get_funds_flow(self,
                             address: str,
                             intermediate_addresses: Optional[list[str]],
                             hops: Optional[int],
                             start_block_height: Optional[int],
                             end_block_height: Optional[int]) -> dict:
            pass

    async def get_balance_tracking(self,
                                   addresses: Optional[list[str]],
                                   min_amount: Optional[int],
                                   max_amount: Optional[int],
                                   start_block_height: Optional[int],
                                   end_block_height: Optional[int]) -> dict:
        """
        WITH ['INTERMEDIATE_ADDRESS_1', 'INTERMEDIATE_ADDRESS_2', 'INTERMEDIATE_ADDRESS_3'] AS intermediates
        MATCH (start:Address {address: '1EkKwjuzYNk6YCDiMhSXjA7BLcgQp9GyCu'})<-[:SENT]-(t:Transaction)-[r:SENT]->(a:Address)
        WHERE a.address = intermediates[0] // Ensuring first intermediate is matched
        WITH start, t, r, a, intermediates
        UNWIND RANGE(1, SIZE(intermediates)-1) AS idx
        MATCH (prev:Address {address: intermediates[idx-1]})-[r2:SENT]->(next:Address {address: intermediates[idx]})
        WITH start, t, r, prev, next, intermediates
        MATCH path = (next)-[r3:SENT*1..5]->(final:Address) // Continue after final intermediate
        RETURN start, t, r, prev, next, path
        """
        pass

    async def get_balance_tracking_timestamp(self,
                                             start_block_height: Optional[int],
                                             end_block_height: Optional[int]) -> dict:
            pass