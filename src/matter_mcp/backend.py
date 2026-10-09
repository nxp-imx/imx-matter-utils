# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

"""Backend abstraction between server.py and live Matter access.

server.py does all validation (node/endpoint/cluster/attribute/command
existence via the Registry and cluster_map). A backend runs only after that
validation passes, so it handles real-time attribute values and command
execution and never touches the node registry.

Both MockBackend and ChipToolBackend implement the same two-method contract,
so either can be swapped in without changing server.py.
"""

from __future__ import annotations

import abc


class MatterBackend(abc.ABC):
    """Contract for live attribute reads and command execution."""

    @abc.abstractmethod
    def read_attribute(
        self, node_id: int, endpoint: int, cluster: str, attribute: str
    ) -> dict:
        """Return the live value as ``{"ok": True, "value": <val>}``."""
        ...

    @abc.abstractmethod
    def invoke_command(
        self, node_id: int, endpoint: int, cluster: str, command: str, args: dict
    ) -> dict:
        """Execute a command; return ``{"ok": True, "status": "SUCCESS"}``."""
        ...
