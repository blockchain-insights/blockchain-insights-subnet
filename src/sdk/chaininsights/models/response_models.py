from pydantic import BaseModel
from typing import Optional, List, Any, Union


class GraphResponse(BaseModel):
    nodes: List[Any]
    edges: List[Any]


class ValidationError(BaseModel):
    loc: List[Any]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    detail: Optional[List[ValidationError]]


class GenericResponse(BaseModel):
    """
    Generic response model to handle both 'json' and 'graph' response types.
    """
    data: Union[dict, GraphResponse]
    message: Optional[str]
