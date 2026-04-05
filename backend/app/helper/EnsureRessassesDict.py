import json

def ensure_dict(extracted_raw):
    if extracted_raw is None:
        return None

    if isinstance(extracted_raw, dict):
        return extracted_raw

    if isinstance(extracted_raw, str):
        try:
            return json.loads(extracted_raw)
        except json.JSONDecodeError:
            raise ValueError("extracted_raw is not valid JSON")

    raise TypeError(f"Unsupported extracted_raw type: {type(extracted_raw)}")