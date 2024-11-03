from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Address(BaseModel):
    id: str
    type: str = Field(default="node")
    label: str = Field(default="address")


class Transaction(BaseModel):
    id: str
    type: str = Field(default="node")
    label: str = Field(default="transaction")
    balance: float
    timestamp: Optional[datetime]
    block_height: Optional[int]


class Edge(BaseModel):
    id: str
    type: str = Field(default="edge")
    label: str
    from_id: str
    to_id: str


class TransactionEntry(BaseModel):
    inputs: List[Dict[str, Any]]  # List of input addresses and amounts
    outputs: List[Dict[str, Any]]  # List of output addresses and amounts
    transaction: Dict[str, Any]    # Transaction details
