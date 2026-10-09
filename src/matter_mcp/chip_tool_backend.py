# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

"""Real Matter backend driving chip-tool interactive server over a WS adapter.

command_map builds the command string, ChipWsAdapter sends it, and
response_parser normalizes the reply. refresh_discovery is a startup pass that
overwrites the registry's discovery layer from the Matter Descriptor cluster.
Transport exceptions become {ok: false, error: chip_error}.
"""

from __future__ import annotations

import logging

from . import command_map, cluster_map, models, response_parser
from .backend import MatterBackend

log = logging.getLogger(__name__)

# Inverse of cluster_map.CLUSTER_IDS: numeric ID -> canonical name.
_ID_TO_NAME: dict[int, str] = {v: k for k, v in cluster_map.CLUSTER_IDS.items()}


class ChipToolBackend(MatterBackend):
    def __init__(self, adapter) -> None:
        self._adapter = adapter

    def read_attribute(self, node_id, endpoint, cluster, attribute) -> dict:
        cmd = command_map.read_command(node_id, endpoint, cluster, attribute)
        if cmd is None:
            return models.error(models.ERR_UNSUPPORTED_ATTRIBUTE)
        try:
            resp = self._adapter.send_command(cmd)
        except Exception as exc:
            log.warning("chip-tool read failed: %s", exc)
            return models.error(models.ERR_CHIP_ERROR)
        result = response_parser.parse_read(resp)
        if result.get("ok") and cluster == "TemperatureMeasurement" and attribute == "MeasuredValue":
            value = result["value"]
            if not isinstance(value, (int, float)):
                # Success row without a numeric value: treat as a chip failure
                # rather than raising an uncaught TypeError on the division.
                return models.error(models.ERR_CHIP_ERROR)
            result = {"ok": True, "value": value / 100}
        return result

    def invoke_command(self, node_id, endpoint, cluster, command, args) -> dict:
        cmd = command_map.invoke_command(node_id, endpoint, cluster, command)
        if cmd is None:
            return models.error(models.ERR_UNSUPPORTED_COMMAND)
        try:
            resp = self._adapter.send_command(cmd)
        except Exception as exc:
            log.warning("chip-tool invoke failed: %s", exc)
            return models.error(models.ERR_CHIP_ERROR)
        return response_parser.parse_command(resp)


def _cluster_name(cluster_id: int) -> str:
    """Map a numeric cluster ID to its canonical name, else keep the number as
    a string (lossless, human-inspectable; support gate stays cluster_map-based)."""
    return _ID_TO_NAME.get(cluster_id, str(cluster_id))


def refresh_discovery(adapter, registry, probe_timeout: float = 5.0) -> None:
    """Overwrite each node's discovery layer from the Matter Descriptor cluster.

    Reads parts-list (endpoints) then server-list (cluster IDs) per endpoint,
    reverse-maps IDs to names, and rewrites node["endpoints"] + sets
    node["discovery"]["source"] = "descriptor". If a node is unreachable (offline
    / not commissioned / mDNS timeout), its hand-written discovery is kept and a
    WARNING is logged. Identity and Annotation layers are untouched. In-memory
    only (no file write-back).

    Probing uses a short per-call timeout (default 5s) with no reconnect retry,
    so an absent node fails fast instead of blocking the whole startup for tens
    of seconds on the WS connect timeout + reconnect.
    """
    for node in registry.iter_nodes():
        node_id = node["node_id"]
        try:
            parts_resp = adapter.send_command_probe(
                command_map.parts_list_command(node_id), probe_timeout
            )
            endpoints = response_parser.parse_descriptor_list(parts_resp)
            if not endpoints:
                log.warning("node %s Descriptor unreachable; keeping manual discovery", node_id)
                continue
            new_endpoints = []
            for ep in endpoints:
                sl_resp = adapter.send_command_probe(
                    command_map.server_list_command(node_id, ep), probe_timeout
                )
                cluster_ids = response_parser.parse_descriptor_list(sl_resp)
                names = [_cluster_name(cid) for cid in cluster_ids]
                new_endpoints.append({"endpoint": ep, "clusters": names})
            node["endpoints"] = new_endpoints
            node.setdefault("discovery", {})["source"] = "descriptor"
        except Exception as exc:
            # Transport failure / short-timeout on this node (e.g. absent device):
            # degrade gracefully, keep the hand-written discovery, move on.
            log.warning("node %s Descriptor refresh failed (%s); keeping manual discovery", node_id, exc)
            continue
