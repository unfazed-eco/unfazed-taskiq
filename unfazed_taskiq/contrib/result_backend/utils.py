"""Helpers for values stored in Tortoise JSONField columns."""

import json
from typing import Any

# When the value cannot be stored as JSON directly, wrap str(value) in a one-key dict.
TASKIQ_JSON_STR_FALLBACK_KEY = "__taskiq_json_str_fallback__"


def encode_for_json_field(value: Any) -> Any:
    """Encode a Python value for Tortoise JSONField.

    Tortoise treats ``str`` as JSON *text* to parse, so arbitrary strings must not be
    passed through bare. JSON-serializable scalars and containers are stored as-is;
    otherwise ``{TASKIQ_JSON_STR_FALLBACK_KEY: str(value)}`` is used.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return {TASKIQ_JSON_STR_FALLBACK_KEY: value}
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return {TASKIQ_JSON_STR_FALLBACK_KEY: str(value)}
