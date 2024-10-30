from datetime import datetime
from typing import Optional
from src.subnet.protocol import MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator.validator import Validator


class BalanceTrackingQueryAPI:
    def __init__(self, validator: Validator):
        super().__init__()
        self.validator = validator

    async def _execute_query(self, network: str, query: str, model_kind = MODEL_KIND_BALANCE_TRACKING) -> dict:
        try:
            data = await self.validator.query_miner(network, model_kind, query, miner_key=None)
            return data
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    async def get_balance_tracking(self,
                                   network: str,
                                   addresses: Optional[list[str]] = None,
                                   min_amount: Optional[int] = None,
                                   max_amount: Optional[int] = None,
                                   start_block_height: Optional[int] = None,
                                   end_block_height: Optional[int] = None,
                                   start_timestamp: Optional[int] = None,
                                   end_timestamp: Optional[int] = None,
                                   page: int = 1,
                                   page_size: int = 100
                                   ) -> dict:
        """
        Get paginated balance tracking data filtered by addresses, amount range, block range, and timestamp range.

        Parameters:
        - network: Network identifier
        - addresses: List of addresses to filter (optional)
        - min_amount: Minimum balance amount to filter (optional)
        - max_amount: Maximum balance amount to filter (optional)
        - start_block_height: Start block height to filter (optional)
        - end_block_height: End block height to filter (optional)
        - start_timestamp: Start timestamp to filter (optional)
        - end_timestamp: End timestamp to filter (optional)
        - page: Page number (default: 1)
        - page_size: Number of items per page (default: 100)

        Returns:
        - A dictionary containing:
            - data: List of balance tracking records
            - total_pages: Total number of pages
            - total_items: Total number of items matching the filters
        """

        base_query = """
            SELECT
                bc.address,
                bc.block as block_height,
                bc.d_balance as balance_delta,
                bc.block_timestamp as timestamp
            FROM
                balance_changes bc
            WHERE
                1=1
        """


        count_query = """
            SELECT MAX(bc.block) - MIN(bc.block) + 1 as total
            FROM balance_changes bc
            WHERE 1=1
        """

        conditions = []

        if addresses:
            formatted_addresses = ', '.join(f"'{address}'" for address in addresses)
            conditions.append(f"bc.address IN ({formatted_addresses})")

        if min_amount is not None:
            conditions.append(f"bc.d_balance >= {min_amount}")
        if max_amount is not None:
            conditions.append(f"bc.d_balance <= {max_amount}")

        if start_block_height is not None:
            conditions.append(f"bc.block >= {start_block_height}")
        if end_block_height is not None:
            conditions.append(f"bc.block <= {end_block_height}")

        if start_timestamp is not None:
            conditions.append(f"bc.block_timestamp >= {start_timestamp}")
        if end_timestamp is not None:
            conditions.append(f"bc.block_timestamp <= {end_timestamp}")

        for condition in conditions:
            base_query += f" AND {condition}"
            count_query += f" AND {condition}"

        offset = (page - 1) * page_size

        base_query += f"""
            ORDER BY bc.block_timestamp
            LIMIT {page_size}
            OFFSET {offset};
        """

        data = await self._execute_query(network, base_query, model_kind=MODEL_KIND_BALANCE_TRACKING)
        total_count = await self._execute_query(network, count_query, model_kind=MODEL_KIND_BALANCE_TRACKING)

        total_items = total_count['response'][0]['total']
        total_pages = (total_items + page_size - 1) // page_size

        return {
            **data,
            'total_pages': total_pages,
            'total_items': total_items
        }

    async def get_balance_tracking_timestamp(self,
                                             network: str,
                                             start_date: Optional[str] = None,
                                             end_date: Optional[str] = None,
                                             page: int = 1,
                                             page_size: int = 100) -> dict:
        base_query = """
            SELECT
                block_height,
                timestamp
            FROM
                blocks
        """

        count_query = """
            SELECT COUNT(*) as total
            FROM blocks
        """

        conditions = []

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

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            base_query += where_clause
            count_query += where_clause

        offset = (page - 1) * page_size
        base_query += f"""
            ORDER BY timestamp
            LIMIT {page_size}
            OFFSET {offset};
        """

        data = await self._execute_query(network, base_query)
        total_count = await self._execute_query(network, count_query)

        total_items = total_count[0]['total']
        total_pages = (total_items + page_size - 1) // page_size

        return {
            'data': data,
            'total_pages': total_pages,
            'total_items': total_items
        }