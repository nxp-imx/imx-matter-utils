"""In-memory MockBackend for development and tests.

Simulates live Matter access with a dict keyed by
``(node_id, endpoint, cluster, attribute)``. OnOff On/Off commands mutate the
stored OnOff attribute so a later read reflects the change. Validation is
server.py's job, so unknown commands and missing attribute keys are handled
leniently rather than as error paths.
"""

from __future__ import annotations

from matter_mcp.backend import MatterBackend


class MockBackend(MatterBackend):
    """Backend backed by an in-memory attribute store."""

    def __init__(self) -> None:
        self._state: dict = {
            (1, 1, "OnOff", "OnOff"): False,
            (2, 1, "TemperatureMeasurement", "MeasuredValue"): 26.5,
        }

    def read_attribute(
        self, node_id: int, endpoint: int, cluster: str, attribute: str
    ) -> dict:
        value = self._state.get((node_id, endpoint, cluster, attribute))
        return {"ok": True, "value": value}

    def invoke_command(
        self, node_id: int, endpoint: int, cluster: str, command: str, args: dict
    ) -> dict:
        if cluster == "OnOff" and command in ("On", "Off"):
            self._state[(node_id, endpoint, "OnOff", "OnOff")] = command == "On"
        return {"ok": True, "status": "SUCCESS"}
