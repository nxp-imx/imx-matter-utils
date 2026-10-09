"""Pure parsers for chip-tool interactive-server WebSocket responses.

Input is the already-decoded dict (json.loads of one WS frame), shaped
``{"results": [...], "logs": [...]}``. These functions do no I/O and no
semantic conversion (e.g. temperature /100 belongs to the backend, not here).
They only normalize the wire response into the project's {ok, ...} shape.
"""

from __future__ import annotations

from . import models

# chip-tool error string -> project error code. Anything not listed -> chip_error.
_ERROR_MAP: dict[str, str] = {
    "UNSUPPORTED_CLUSTER": models.ERR_UNSUPPORTED_CLUSTER,
    "UNSUPPORTED_ENDPOINT": models.ERR_UNKNOWN_ENDPOINT,
    "UNSUPPORTED_ATTRIBUTE": models.ERR_UNSUPPORTED_ATTRIBUTE,
}


def _map_error(code: str) -> str:
    return _ERROR_MAP.get(code, models.ERR_CHIP_ERROR)


def parse_read(resp: dict) -> dict:
    """Normalize an attribute-read response.

    Success -> {"ok": True, "value": <native value>}.
    Error row -> {"ok": False, "error": <mapped code>}.
    Empty/missing results -> {"ok": False, "error": "chip_error"}.
    """
    results = resp.get("results")
    if not results:
        return models.error(models.ERR_CHIP_ERROR)
    row = results[0]
    if "error" in row:
        return models.error(_map_error(row["error"]))
    return {"ok": True, "value": row.get("value")}


def parse_command(resp: dict) -> dict:
    """Normalize a command-invoke response.

    Empty results (or a result row with no error) -> success.
    Error row -> mapped error. Missing results key -> chip_error.
    """
    results = resp.get("results")
    if results is None:
        return models.error(models.ERR_CHIP_ERROR)
    if len(results) == 0:
        return {"ok": True, "status": "SUCCESS"}
    row = results[0]
    if "error" in row:
        return models.error(_map_error(row["error"]))
    return {"ok": True, "status": "SUCCESS"}


def parse_descriptor_list(resp: dict) -> list:
    """Extract the value array from a Descriptor read (parts-list / server-list).

    Returns the raw list (endpoint numbers or cluster IDs). On any failure or
    missing data, returns an empty list so the caller can fall back safely.
    """
    results = resp.get("results")
    if not results:
        return []
    row = results[0]
    if "error" in row:
        return []
    value = row.get("value")
    return value if isinstance(value, list) else []
