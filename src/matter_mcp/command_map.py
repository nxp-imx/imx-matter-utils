# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

"""Static Matter-name -> chip-tool command-string builders.

MVP scope (OnOff + TemperatureMeasurement) uses a fixed lookup instead of a
generic PascalCase->kebab converter (YAGNI). A builder returns None for any
(cluster, attribute/command) pair outside the map; the backend maps None to
the appropriate unsupported_* error code.
"""

from __future__ import annotations

# (cluster, attribute) -> "<cluster-lc> read <attr-kebab>"
_READ_TEMPLATES: dict[tuple[str, str], str] = {
    ("OnOff", "OnOff"): "onoff read on-off",
    ("TemperatureMeasurement", "MeasuredValue"): "temperaturemeasurement read measured-value",
}

# (cluster, command) -> "<cluster-lc> <command-lc>"
_INVOKE_TEMPLATES: dict[tuple[str, str], str] = {
    ("OnOff", "On"): "onoff on",
    ("OnOff", "Off"): "onoff off",
    ("OnOff", "Toggle"): "onoff toggle",
}


def read_command(node_id: int, endpoint: int, cluster: str, attribute: str) -> str | None:
    """Build the chip-tool read command string, or None if the pair is unsupported."""
    prefix = _READ_TEMPLATES.get((cluster, attribute))
    if prefix is None:
        return None
    return f"{prefix} {node_id} {endpoint}"


def invoke_command(node_id: int, endpoint: int, cluster: str, command: str) -> str | None:
    """Build the chip-tool invoke command string, or None if unsupported."""
    prefix = _INVOKE_TEMPLATES.get((cluster, command))
    if prefix is None:
        return None
    return f"{prefix} {node_id} {endpoint}"


def parts_list_command(node_id: int) -> str:
    """Descriptor parts-list read (endpoints), always on endpoint 0."""
    return f"descriptor read parts-list {node_id} 0"


def server_list_command(node_id: int, endpoint: int) -> str:
    """Descriptor server-list read (cluster IDs) for one endpoint."""
    return f"descriptor read server-list {node_id} {endpoint}"
