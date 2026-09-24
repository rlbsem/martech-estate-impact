import json


def parse(text):
    data = json.loads(text)
    if (
        not isinstance(data, dict)
        or data.get("format") != "stewardship/v1"
        or not isinstance(data.get("assertions"), list)
    ):
        raise ValueError("unsupported stewardship format")
    return [dict(row, location=f"/assertions/{i}") for i, row in enumerate(data["assertions"])]
