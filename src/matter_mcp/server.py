"""FastMCP server exposing 4 Matter tools over stdio.

Each tool validates its arguments, calls the backend, then shapes the output.
The logic lives in plain `*_impl(ctx, ...)` functions so tests can call them
directly; the @mcp.tool wrappers are thin adapters over a module-level context.
"""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import cluster_map, models
from .backend import MatterBackend
from .mock_backend import MockBackend
from .registry import Registry
from .chip_ws_adapter import ChipWsAdapter
from .chip_tool_backend import ChipToolBackend, refresh_discovery


class ToolContext:
    def __init__(self, registry: Registry, backend: MatterBackend) -> None:
        self.registry = registry
        self.backend = backend


def _validate_target(ctx: ToolContext, node_id, endpoint, cluster) -> str | None:
    if ctx.registry.get_node(node_id) is None:
        return models.ERR_UNKNOWN_NODE
    if not ctx.registry.has_endpoint(node_id, endpoint):
        return models.ERR_UNKNOWN_ENDPOINT
    if not ctx.registry.endpoint_has_cluster(node_id, endpoint, cluster):
        return models.ERR_UNSUPPORTED_CLUSTER
    return None


def list_nodes_impl(ctx: ToolContext) -> dict:
    return {"ok": True, "nodes": ctx.registry.list_nodes()}


def describe_node_impl(ctx: ToolContext, node_id: int) -> dict:
    node = ctx.registry.get_node(node_id)
    if node is None:
        return models.error(models.ERR_UNKNOWN_NODE)
    return {
        "ok": True,
        "node_id": node_id,
        "label": node.get("label"),
        "endpoints": node["endpoints"],
    }


def read_attribute_impl(ctx: ToolContext, node_id, endpoint, cluster, attribute) -> dict:
    err = _validate_target(ctx, node_id, endpoint, cluster)
    if err:
        return models.error(err)
    if not cluster_map.is_supported_attribute(cluster, attribute):
        return models.error(models.ERR_UNSUPPORTED_ATTRIBUTE)
    res = ctx.backend.read_attribute(node_id, endpoint, cluster, attribute)
    if not res.get("ok"):
        return models.error(res.get("error", "chip_error"))
    value = res["value"]
    label = ctx.registry.get_node(node_id).get("label", f"node {node_id}")
    summary = _summarize_read(label, cluster, attribute, value)
    return {"ok": True, "value": value, "summary": summary}


def invoke_command_impl(ctx: ToolContext, node_id, endpoint, cluster, command, args) -> dict:
    err = _validate_target(ctx, node_id, endpoint, cluster)
    if err:
        return models.error(err)
    if not cluster_map.is_supported_command(cluster, command):
        return models.error(models.ERR_UNSUPPORTED_COMMAND)
    res = ctx.backend.invoke_command(node_id, endpoint, cluster, command, args or {})
    if not res.get("ok"):
        return models.error(res.get("error", "chip_error"))
    label = ctx.registry.get_node(node_id).get("label", f"node {node_id}")
    summary = _summarize_invoke(label, cluster, command)
    return {"ok": True, "status": "SUCCESS", "summary": summary}


def _summarize_read(label, cluster, attribute, value) -> str:
    if cluster == "OnOff":
        return f"{label} is {'on' if value else 'off'}"
    if cluster == "TemperatureMeasurement":
        return f"{label} temperature is {value} C"
    return f"{label} {cluster}.{attribute} = {value}"


def _summarize_invoke(label, cluster, command) -> str:
    if cluster == "OnOff":
        return f"{label} has been turned {'on' if command == 'On' else 'off'}"
    return f"{label} {cluster}.{command} executed"


def _default_registry_path() -> str:
    """Resolve the device-registry path.

    Resolution order:
      1. ``MATTER_MCP_REGISTRY`` env var (explicit override, always wins).
      2. ``MATTER_MCP_CONFIG_DIR``/device_registry.json if that env var is set.
      3. The system config dir ``/etc/matter-mcp/device_registry.json`` when it
         exists (the packaged / Yocto install layout).
      4. The in-repo ``config/device_registry.json`` as a dev fallback so the
         test suite and a git checkout keep working without installation.
    """
    override = os.environ.get("MATTER_MCP_REGISTRY")
    if override:
        return override

    config_dir = os.environ.get("MATTER_MCP_CONFIG_DIR")
    if config_dir:
        return str(Path(config_dir) / "device_registry.json")

    system_path = Path("/etc/matter-mcp/device_registry.json")
    if system_path.exists():
        return str(system_path)

    return str(Path(__file__).resolve().parents[2] / "config" / "device_registry.json")


def _default_context() -> ToolContext:
    registry = Registry.load(_default_registry_path())
    backend_kind = os.environ.get("MATTER_MCP_BACKEND", "chiptool")  # default = real device
    if backend_kind == "mock":
        backend = MockBackend()
    else:
        url = os.environ.get("MATTER_MCP_CHIP_WS_URL", "ws://127.0.0.1:9002")
        timeout = float(os.environ.get("MATTER_MCP_CHIP_WS_TIMEOUT", "30"))
        adapter = ChipWsAdapter(url, timeout=timeout)
        adapter.connect()
        refresh_discovery(adapter, registry)  # startup discovery; fast-skips unreachable nodes
        backend = ChipToolBackend(adapter)
    return ToolContext(registry, backend)


mcp = FastMCP("matter")
_CTX: ToolContext | None = None


def _ctx() -> ToolContext:
    global _CTX
    if _CTX is None:
        _CTX = _default_context()
    return _CTX


@mcp.tool()
def matter_list_nodes() -> dict:
    """List all known Matter nodes (from the registry). Use when the user asks
    what devices are available or you need a node_id."""
    return list_nodes_impl(_ctx())


@mcp.tool()
def matter_describe_node(node_id: int) -> dict:
    """Describe a node's endpoints, device types, and clusters. Use when node
    capability is unclear before reading or commanding."""
    return describe_node_impl(_ctx(), node_id)


@mcp.tool()
def matter_read_attribute(node_id: int, endpoint: int, cluster: str, attribute: str) -> dict:
    """Read a Matter attribute. Supports OnOff.OnOff and
    TemperatureMeasurement.MeasuredValue. Use for read-only questions."""
    return read_attribute_impl(_ctx(), node_id, endpoint, cluster, attribute)


@mcp.tool()
def matter_invoke_command(node_id: int, endpoint: int, cluster: str, command: str, args: dict | None = None) -> dict:
    """Invoke a Matter command. Supports OnOff.On and OnOff.Off. Use only for
    device control when the target is clear."""
    return invoke_command_impl(_ctx(), node_id, endpoint, cluster, command, args or {})


def main() -> None:
    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()
