from typing import List, Dict, Any
from src.subnet.miner.blockchain import BaseTabularTransformer


class BitcoinTabularTransformer(BaseTabularTransformer):
    @staticmethod
    def transform_result_set(result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        print(result)  # Log the result structure for inspection
        if not result:
            return [{"columns": [], "rows": []}]

        # Dynamically generate columns based on the keys in the first result item
        columns = [{"name": key, "label": key.title()} for key in result[0].keys()]

        # Populate the content based on the result set
        rows = [{**item} for item in result]

        return [{"columns": columns, "rows": rows}]
