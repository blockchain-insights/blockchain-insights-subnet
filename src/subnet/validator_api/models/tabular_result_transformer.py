from src.subnet.validator_api.models import BaseTabularTransformer
from typing import List, Any, Dict
from loguru import logger

class TabularTransformer(BaseTabularTransformer):
   def transform_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug(result)  # Log the result structure for inspection
        if not result:
            return [{"columns": [], "rows": []}]

        # Dynamically generate columns based on the keys in the first result item
        columns = [{"name": key, "label": key.title()} for key in result['data'][0].keys()]

        # Populate the content based on the result set
        rows = [{**item} for item in result] #TODO: tu nie dziala

        return [{"columns": columns, "rows": rows}]
