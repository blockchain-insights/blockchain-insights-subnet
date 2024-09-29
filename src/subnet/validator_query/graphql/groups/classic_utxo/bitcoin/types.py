import strawberry
from typing import List, Optional


@strawberry.type
class Transaction:
    """
    Represents a Bitcoin transaction.
    """
    tx_id: str
    timestamp: str
    in_total_amount: float
    out_total_amount: float
    block_height: int
    is_coinbase: bool

    # Addresses that sent funds to this transaction
    sent_from_addresses: List["Address"] = []

    # Addresses that received funds from this transaction
    sent_to_addresses: List["Address"] = []


@strawberry.type
class Address:
    """
    Represents a Bitcoin address.
    """
    address: str

    # Transactions where this address sent funds
    sent_transactions: List[Transaction] = []

    # Transactions where this address received funds
    received_transactions: List[Transaction] = []


@strawberry.type
class Block:
    """
    Represents a Bitcoin block.
    """
    id: int
    height: int
    timestamp: str

    # Transactions included in this block
    transactions: List[Transaction] = []
