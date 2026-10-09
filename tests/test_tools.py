# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

from matter_mcp.mock_backend import MockBackend
from matter_mcp.registry import Registry
from matter_mcp import server

REG_PATH = Path(__file__).resolve().parents[1] / "config" / "device_registry.json"


@pytest.fixture
def ctx():
    return server.ToolContext(Registry.load(REG_PATH), MockBackend())


def test_list_nodes(ctx):
    out = server.list_nodes_impl(ctx)
    assert out["ok"] is True
    assert sorted(n["node_id"] for n in out["nodes"]) == [1]


def test_describe_node_ok(ctx):
    out = server.describe_node_impl(ctx, 1)
    assert out["ok"] is True
    assert out["label"] == "lab_light"
    # Full endpoint shape per spec §6.2: {endpoint, device_type, clusters}
    assert out["endpoints"][0] == {
        "endpoint": 1,
        "device_type": "DimmableLight",
        "clusters": ["OnOff", "LevelControl"],
    }


def test_describe_node_unknown(ctx):
    assert server.describe_node_impl(ctx, 999) == {"ok": False, "error": "unknown_node"}


def test_read_onoff_default_false(ctx):
    out = server.read_attribute_impl(ctx, 1, 1, "OnOff", "OnOff")
    assert out["ok"] is True
    assert out["value"] is False
    assert "lab_light" in out["summary"]


def test_read_removed_temp_node_is_unknown(ctx):
    # node 2 (the mock temperature sensor) was removed from the registry once we
    # switched to the single real light; it must now resolve to unknown_node.
    out = server.read_attribute_impl(ctx, 2, 1, "TemperatureMeasurement", "MeasuredValue")
    assert out["error"] == "unknown_node"


def test_read_unknown_node(ctx):
    assert server.read_attribute_impl(ctx, 999, 1, "OnOff", "OnOff")["error"] == "unknown_node"


def test_read_unknown_endpoint(ctx):
    assert server.read_attribute_impl(ctx, 1, 9, "OnOff", "OnOff")["error"] == "unknown_endpoint"


def test_read_unsupported_cluster(ctx):
    assert server.read_attribute_impl(ctx, 1, 1, "DoorLock", "LockState")["error"] == "unsupported_cluster"


def test_read_unsupported_attribute(ctx):
    assert server.read_attribute_impl(ctx, 1, 1, "OnOff", "Nope")["error"] == "unsupported_attribute"


def test_invoke_on_updates_state(ctx):
    out = server.invoke_command_impl(ctx, 1, 1, "OnOff", "On", {})
    assert out["ok"] is True
    assert out["status"] == "SUCCESS"
    assert server.read_attribute_impl(ctx, 1, 1, "OnOff", "OnOff")["value"] is True


def test_invoke_unsupported_command(ctx):
    assert server.invoke_command_impl(ctx, 1, 1, "OnOff", "GlobalSceneControl", {})["error"] == "unsupported_command"


def test_invoke_unknown_node(ctx):
    assert server.invoke_command_impl(ctx, 999, 1, "OnOff", "On", {})["error"] == "unknown_node"


class _FailingBackend:
    """Backend stub that always reports failure (simulates a real read/invoke error)."""
    def read_attribute(self, node_id, endpoint, cluster, attribute):
        return {"ok": False, "error": "chip_error"}
    def invoke_command(self, node_id, endpoint, cluster, command, args):
        return {"ok": False, "error": "chip_error"}


def test_read_attribute_passes_through_backend_failure():
    from matter_mcp import server
    from matter_mcp.registry import Registry
    reg = Registry.load(REG_PATH)
    ctx = server.ToolContext(reg, _FailingBackend())
    out = server.read_attribute_impl(ctx, 1, 1, "OnOff", "OnOff")
    assert out == {"ok": False, "error": "chip_error"}


def test_invoke_command_passes_through_backend_failure():
    from matter_mcp import server
    from matter_mcp.registry import Registry
    reg = Registry.load(REG_PATH)
    ctx = server.ToolContext(reg, _FailingBackend())
    out = server.invoke_command_impl(ctx, 1, 1, "OnOff", "On", {})
    assert out == {"ok": False, "error": "chip_error"}

def test_default_context_uses_mock_when_env_set(monkeypatch):
    from matter_mcp import server
    from matter_mcp.mock_backend import MockBackend
    monkeypatch.setenv("MATTER_MCP_BACKEND", "mock")
    ctx = server._default_context()
    assert isinstance(ctx.backend, MockBackend)


def test_default_context_uses_chiptool_by_default(monkeypatch):
    from matter_mcp import server
    from matter_mcp.chip_tool_backend import ChipToolBackend
    monkeypatch.delenv("MATTER_MCP_BACKEND", raising=False)

    class _StubAdapter:
        def __init__(self, url, timeout=30.0):
            self.url = url
            self.timeout = timeout
        def connect(self):
            pass
    monkeypatch.setattr(server, "ChipWsAdapter", _StubAdapter, raising=False)
    monkeypatch.setattr(server, "refresh_discovery", lambda a, r: None, raising=False)

    ctx = server._default_context()
    assert isinstance(ctx.backend, ChipToolBackend)
