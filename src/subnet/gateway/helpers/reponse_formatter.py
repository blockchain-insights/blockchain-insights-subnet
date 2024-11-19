from enum import Enum
from fastapi.responses import JSONResponse
from datetime import datetime


# ResponseType Enum
class ResponseType(str, Enum):
    json = "json"
    graph = "graph"
    chart = "chart"


def format_response(data: dict, response_type: ResponseType):
    """Helper function to format response based on response_type."""

    def serialize_datetime(obj):
        """Helper function to convert datetime objects to string."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def process_data(data):
        if isinstance(data, dict):
            return {key: process_data(value) for key, value in data.items() if value is not None}
        elif isinstance(data, list):
            return [process_data(item) for item in data if item is not None]
        else:
            return serialize_datetime(data)

    processed_data = process_data(data)

    if response_type == ResponseType.graph:
        return JSONResponse(content=processed_data, media_type="application/vnd.graph+json")

    if response_type == ResponseType.chart:
        return JSONResponse(content=processed_data, media_type="application/vnd.chart+json")

    return JSONResponse(content=processed_data)
