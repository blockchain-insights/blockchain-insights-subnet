import strawberry
from typing import List

from fastapi import HTTPException
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI, HTTPException, Request


@strawberry.type
class Transaction:
    tx_id: str
    timestamp: str


@strawberry.type
class Block:
    id: int
    height: str
    transactions: List[Transaction]


@strawberry.type
class Query:

    @strawberry.field
    async def classic_utxo_get_transaction(self, network: str, tx_id: str) -> Transaction:
        return Transaction(tx_id="asdf", timestamp="2021-10-10")

    @strawberry.field
    async def classic_utxo_get_block(self, network: str, block_height: str) -> Block:
        return Block(id=1, height="100", transactions=[Transaction(tx_id="asdf", timestamp="2021-10-10")])


schema = strawberry.Schema(query=Query)


async def get_graphql_context(request: Request) -> dict:
    api_key = request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key in query parameters")

    return {"api_key": api_key}

graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
