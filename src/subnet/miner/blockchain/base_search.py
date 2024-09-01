class BaseGraphSearch:
    def execute_query(self, query: str):
        """Execute a query and return the result."""

    def execute_cypher_query(self, cypher_query: str):
        """Execute a cypher query and return the result."""

    def solve_challenge(self, in_total_amount: int, out_total_amount: int, tx_id_last_6_chars: str) -> str:
        """Solve a challenge and return the result."""

    def close(self):
        """Close the connection to the graph database."""


class BaseBalanceSearch:
    def execute_query(self, query: str):
        """Execute a query and return the result."""

    def solve_challenge(self, block_heights: list[int]):
        """Solve a challenge and return the result."""
