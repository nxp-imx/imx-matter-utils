# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

import pytest
from matter_mcp.chip_tool_backend import ChipToolBackend, refresh_discovery
from matter_mcp.backend import MatterBackend
from matter_mcp.registry import Registry


class _FakeAdapter:
    """Returns a queued/keyed response dict per command string."""
    def __init__(self, responses=None, raise_exc=False):
        self._responses = responses or {}
        self._raise = raise_exc
        self.sent = []

    def send_command(self, cmd):
        self.sent.append(cmd)
        if self._raise:
            raise ConnectionError("ws down")
        return self._responses[cmd]

    def send_command_probe(self, cmd, timeout):
        return self.send_command(cmd)


def test_is_a_matter_backend():
    assert issubclass(ChipToolBackend, MatterBackend)
    assert isinstance(ChipToolBackend(_FakeAdapter()), MatterBackend)


def test_read_onoff_returns_bool():
    resp = {"results": [{"clusterId": 6, "endpointId": 1, "value": False}]}
    a = _FakeAdapter({"onoff read on-off 1 1": resp})
    b = ChipToolBackend(a)
    assert b.read_attribute(1, 1, "OnOff", "OnOff") == {"ok": True, "value": False}


def test_read_temperature_divides_by_100():
    resp = {"results": [{"clusterId": 1026, "endpointId": 1, "value": 2650}]}
    a = _FakeAdapter({"temperaturemeasurement read measured-value 2 1": resp})
    b = ChipToolBackend(a)
    out = b.read_attribute(2, 1, "TemperatureMeasurement", "MeasuredValue")
    assert out == {"ok": True, "value": 26.5}


def test_read_temperature_none_value_is_chip_error():
    """A success row missing a numeric value must not raise TypeError on /100."""
    resp = {"results": [{"clusterId": 1026, "endpointId": 1}]}
    a = _FakeAdapter({"temperaturemeasurement read measured-value 2 1": resp})
    b = ChipToolBackend(a)
    out = b.read_attribute(2, 1, "TemperatureMeasurement", "MeasuredValue")
    assert out == {"ok": False, "error": "chip_error"}


def test_read_unsupported_pair_returns_unsupported_attribute():
    a = _FakeAdapter({})
    b = ChipToolBackend(a)
    assert b.read_attribute(1, 1, "LevelControl", "CurrentLevel") == \
        {"ok": False, "error": "unsupported_attribute"}
    assert a.sent == []


def test_read_chip_error_maps():
    resp = {"results": [{"error": "UNSUPPORTED_CLUSTER"}, {"error": "FAILURE"}]}
    a = _FakeAdapter({"onoff read on-off 1 1": resp})
    b = ChipToolBackend(a)
    assert b.read_attribute(1, 1, "OnOff", "OnOff") == \
        {"ok": False, "error": "unsupported_cluster"}


def test_read_transport_exception_is_chip_error():
    a = _FakeAdapter(raise_exc=True)
    b = ChipToolBackend(a)
    assert b.read_attribute(1, 1, "OnOff", "OnOff") == {"ok": False, "error": "chip_error"}


def test_invoke_on_returns_success():
    a = _FakeAdapter({"onoff on 1 1": {"results": []}})
    b = ChipToolBackend(a)
    assert b.invoke_command(1, 1, "OnOff", "On", {}) == {"ok": True, "status": "SUCCESS"}


def test_invoke_unsupported_returns_unsupported_command():
    a = _FakeAdapter({})
    b = ChipToolBackend(a)
    assert b.invoke_command(1, 1, "OnOff", "GlobalSceneControl", {}) == \
        {"ok": False, "error": "unsupported_command"}
    assert a.sent == []


def test_invoke_transport_exception_is_chip_error():
    a = _FakeAdapter(raise_exc=True)
    b = ChipToolBackend(a)
    assert b.invoke_command(1, 1, "OnOff", "On", {}) == {"ok": False, "error": "chip_error"}


def _reg_with_two_nodes():
    return Registry([
        {"node_id": 1, "commissioned": True, "label": "lab_light", "type": "light",
         "room": "lab", "discovery": {"source": "manual"},
         "endpoints": [{"endpoint": 1, "device_type": "DimmableLight",
                        "clusters": ["OnOff", "LevelControl"]}]},
        {"node_id": 2, "commissioned": True, "label": "lab_temp", "type": "sensor",
         "room": "lab", "discovery": {"source": "manual"},
         "endpoints": [{"endpoint": 1, "device_type": "TemperatureSensor",
                        "clusters": ["TemperatureMeasurement"]}]},
    ])


def test_refresh_discovery_overwrites_from_descriptor():
    reg = _reg_with_two_nodes()
    responses = {
        "descriptor read parts-list 1 0": {"results": [{"value": [1]}]},
        "descriptor read server-list 1 1": {"results": [{"value": [6, 8]}]},
        "descriptor read parts-list 2 0": {"results": [{"value": [1]}]},
        "descriptor read server-list 2 1": {"results": [{"value": [1026]}]},
    }
    refresh_discovery(_FakeAdapter(responses), reg)
    n1 = reg.get_node(1)
    assert n1["discovery"]["source"] == "descriptor"
    assert n1["endpoints"] == [{"endpoint": 1, "clusters": ["OnOff", "LevelControl"]}]
    n2 = reg.get_node(2)
    assert n2["endpoints"] == [{"endpoint": 1, "clusters": ["TemperatureMeasurement"]}]
    assert n1["label"] == "lab_light" and n1["commissioned"] is True


def test_refresh_discovery_keeps_manual_when_node_unreachable():
    reg = _reg_with_two_nodes()
    responses = {
        "descriptor read parts-list 1 0": {"results": [{"error": "TIMEOUT"}]},
        "descriptor read parts-list 2 0": {"results": [{"value": [1]}]},
        "descriptor read server-list 2 1": {"results": [{"value": [1026]}]},
    }
    refresh_discovery(_FakeAdapter(responses), reg)
    n1 = reg.get_node(1)
    assert n1["discovery"]["source"] == "manual"
    assert n1["endpoints"][0]["clusters"] == ["OnOff", "LevelControl"]
    n2 = reg.get_node(2)
    assert n2["discovery"]["source"] == "descriptor"


def test_refresh_discovery_keeps_unknown_cluster_ids_as_strings():
    reg = _reg_with_two_nodes()
    responses = {
        "descriptor read parts-list 1 0": {"results": [{"value": [1]}]},
        "descriptor read server-list 1 1": {"results": [{"value": [29, 6, 768]}]},
        "descriptor read parts-list 2 0": {"results": [{"value": []}]},
    }
    refresh_discovery(_FakeAdapter(responses), reg)
    clusters = reg.get_node(1)["endpoints"][0]["clusters"]
    assert clusters == ["29", "OnOff", "768"]


def test_refresh_discovery_keeps_manual_when_send_raises():
    """A raised transport error on one node must degrade gracefully (keep manual)
    and still process the remaining nodes."""
    reg = _reg_with_two_nodes()

    class _PartlyRaisingAdapter:
        def __init__(self):
            self.sent = []

        def send_command(self, cmd):
            self.sent.append(cmd)
            if cmd == "descriptor read parts-list 1 0":
                raise ConnectionError("cold-start timeout")
            responses = {
                "descriptor read parts-list 2 0": {"results": [{"value": [1]}]},
                "descriptor read server-list 2 1": {"results": [{"value": [1026]}]},
            }
            return responses[cmd]

        def send_command_probe(self, cmd, timeout):
            return self.send_command(cmd)

    refresh_discovery(_PartlyRaisingAdapter(), reg)
    n1 = reg.get_node(1)
    assert n1["discovery"]["source"] == "manual"
    assert n1["endpoints"][0]["clusters"] == ["OnOff", "LevelControl"]
    n2 = reg.get_node(2)
    assert n2["discovery"]["source"] == "descriptor"
    assert n2["endpoints"] == [{"endpoint": 1, "clusters": ["TemperatureMeasurement"]}]
