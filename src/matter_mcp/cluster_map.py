"""Static Matter cluster/attribute/command support table for the MVP.

Lists which clusters/attributes/commands the MVP supports and their numeric
cluster IDs, shared by the mock and real chip-tool backends.
"""

from __future__ import annotations

# Cluster name -> numeric cluster ID (Matter spec values).
CLUSTER_IDS: dict[str, int] = {
    "OnOff": 6,
    "LevelControl": 8,
    "TemperatureMeasurement": 1026,
    "OccupancySensing": 1030,
}

# Clusters the MVP actively supports operations on.
_SUPPORTED_CLUSTERS: frozenset[str] = frozenset({"OnOff", "TemperatureMeasurement"})

# (cluster, attribute) pairs the MVP supports.
_SUPPORTED_ATTRIBUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("OnOff", "OnOff"),
        ("TemperatureMeasurement", "MeasuredValue"),
    }
)

# (cluster, command) pairs the MVP supports.
_SUPPORTED_COMMANDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("OnOff", "On"),
        ("OnOff", "Off"),
        ("OnOff", "Toggle"),
    }
)


def cluster_id(cluster: str) -> int | None:
    """Return the numeric ID for a cluster name, or None if unknown."""
    return CLUSTER_IDS.get(cluster)


def is_supported_cluster(cluster: str) -> bool:
    """Return True only for clusters the MVP actively supports operations on."""
    return cluster in _SUPPORTED_CLUSTERS


def is_supported_attribute(cluster: str, attribute: str) -> bool:
    """Return True only for MVP-supported (cluster, attribute) pairs."""
    return (cluster, attribute) in _SUPPORTED_ATTRIBUTES


def is_supported_command(cluster: str, command: str) -> bool:
    """Return True only for MVP-supported (cluster, command) pairs."""
    return (cluster, command) in _SUPPORTED_COMMANDS
