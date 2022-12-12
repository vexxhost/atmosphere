import json

import _jsonnet


def load_jsonnet_from_path(path: str) -> any:
    raw = _jsonnet.evaluate_file(path)
    return json.loads(raw)
