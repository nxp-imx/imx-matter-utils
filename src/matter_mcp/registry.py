# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

"""Three-layer device registry holding the node inventory.

chip-tool has no "list nodes" command, so node inventory always comes from a
hand-editable JSON file. Each node has three layers with the same schema in
both the mock and real phases; only the source of the discovery layer differs:

* Identity (human-managed): ``node_id``, ``commissioned``
* Discovery (mock: hand-filled; real: overwritten from the Matter Descriptor
  cluster): ``endpoints`` list and a ``discovery`` block
* Annotation (human-managed): ``label``, ``type``, ``room``
"""

from __future__ import annotations

import json


class Registry:
    """In-memory view over the parsed device registry file."""

    def __init__(self, nodes: list[dict]) -> None:
        self._nodes = nodes

    @classmethod
    def load(cls, path: str) -> "Registry":
        """Read and parse the registry JSON file at ``path``."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(data["nodes"])

    def list_nodes(self) -> list[dict]:
        """Return the compact per-node shape used by ``matter_list_nodes``.

        ``endpoints`` is reduced to a list of endpoint ints, not cluster objects.
        """
        return [
            {
                "node_id": node["node_id"],
                "label": node["label"],
                "type": node["type"],
                "endpoints": [ep["endpoint"] for ep in node["endpoints"]],
            }
            for node in self._nodes
        ]

    def iter_nodes(self) -> list[dict]:
        """Return the full raw node dicts (all layers) for whole-registry passes
        such as Descriptor-based discovery refresh."""
        return self._nodes

    def get_node(self, node_id: int) -> dict | None:
        """Return the full raw node dict (all layers), or None if not found."""
        for node in self._nodes:
            if node["node_id"] == node_id:
                return node
        return None

    def has_endpoint(self, node_id: int, endpoint: int) -> bool:
        """True iff the node exists and has the given endpoint."""
        node = self.get_node(node_id)
        if node is None:
            return False
        return any(ep["endpoint"] == endpoint for ep in node["endpoints"])

    def endpoint_has_cluster(self, node_id: int, endpoint: int, cluster: str) -> bool:
        """True iff the node exists, has the endpoint, and it hosts the cluster."""
        node = self.get_node(node_id)
        if node is None:
            return False
        for ep in node["endpoints"]:
            if ep["endpoint"] == endpoint:
                return cluster in ep["clusters"]
        return False
