import base64
import json


def encode_to_base64(data: dict) -> str:
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_from_base64(encoded: str) -> dict:
    json_str = base64.urlsafe_b64decode(encoded.encode()).decode()
    return json.loads(json_str)
