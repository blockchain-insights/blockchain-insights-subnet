from enum import Enum

from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime

# ResponseType Enum
class ResponseType(str, Enum):
    json = "json"
    graph = "graph"

def format_response(data: dict, response_type: ResponseType):
    """Helper function to format response based on response_type."""

    def serialize_datetime(obj):
        """Helper function to convert datetime objects to string."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    # Recursively walk through the data and convert datetime to string
    def process_data(data):
        if isinstance(data, dict):
            return {key: process_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [process_data(item) for item in data]
        else:
            return serialize_datetime(data)

    processed_data = process_data(data)  # Ensure that datetime objects are handled for JSON or graph response

    if response_type == ResponseType.graph:
        # For graph format, use the processed data and a custom media type
        return JSONResponse(content=processed_data, media_type="application/vnd.graph+json")

    # Default to JSON response
    return JSONResponse(content=processed_data)
