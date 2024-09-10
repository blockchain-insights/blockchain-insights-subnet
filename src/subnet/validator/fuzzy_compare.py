from fuzzywuzzy import fuzz
from collections.abc import MutableMapping


# Function to flatten nested JSON
def flatten_json(json_obj, parent_key='', sep='.'):
    items = []
    for k, v in json_obj.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# Fuzzy comparison function
def fuzzy_json_similarity(json1, json2, numeric_tolerance=0.1, string_threshold=70):
    flat_json1 = flatten_json(json1)
    flat_json2 = flatten_json(json2)

    common_keys = set(flat_json1.keys()).union(set(flat_json2.keys()))

    similarity_score = 0
    total_weight = 0

    for key in common_keys:
        value1 = flat_json1.get(key)
        value2 = flat_json2.get(key)

        if isinstance(value1, str) and isinstance(value2, str):
            # Use fuzzy string matching for strings
            similarity = fuzz.ratio(value1, value2) / 100.0
            if similarity >= string_threshold / 100.0:
                similarity_score += similarity
        elif isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            # Use numeric tolerance for numbers
            diff = abs(value1 - value2)
            max_val = max(abs(value1), abs(value2), 1)
            if diff / max_val <= numeric_tolerance:
                similarity_score += 1  # Consider it similar if within tolerance
            else:
                similarity_score += 1 - (diff / max_val)
        elif value1 is None or value2 is None:
            # Handle missing values
            if value1 == value2:
                similarity_score += 1
        else:
            # No comparison possible, give zero score
            similarity_score += 0

        total_weight += 1

    return similarity_score / total_weight if total_weight else 1

