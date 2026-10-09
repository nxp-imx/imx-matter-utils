"""Tests for the MatterBackend ABC and the in-memory MockBackend.

The backend deals ONLY with live attribute values and command execution. It
does no registry/existence validation -- server.py does that before calling.
The key behavior under test is state coherence: an invoked OnOff command must
be reflected by a subsequent read_attribute of the same OnOff attribute.
"""

import pytest

from matter_mcp.backend import MatterBackend
from matter_mcp.mock_backend import MockBackend


def test_mock_backend_is_a_matter_backend() -> None:
    backend = MockBackend()
    assert isinstance(backend, MatterBackend)


def test_read_seeded_onoff_starts_false() -> None:
    backend = MockBackend()
    assert backend.read_attribute(1, 1, "OnOff", "OnOff") == {
        "ok": True,
        "value": False,
    }


def test_read_seeded_temperature() -> None:
    backend = MockBackend()
    assert backend.read_attribute(2, 1, "TemperatureMeasurement", "MeasuredValue") == {
        "ok": True,
        "value": 26.5,
    }


def test_read_missing_key_returns_none_value() -> None:
    backend = MockBackend()
    assert backend.read_attribute(9, 9, "OnOff", "OnOff") == {
        "ok": True,
        "value": None,
    }


def test_invoke_on_sets_onoff_true() -> None:
    backend = MockBackend()
    assert backend.invoke_command(1, 1, "OnOff", "On", {}) == {
        "ok": True,
        "status": "SUCCESS",
    }
    assert backend.read_attribute(1, 1, "OnOff", "OnOff") == {
        "ok": True,
        "value": True,
    }


def test_invoke_off_sets_onoff_false() -> None:
    backend = MockBackend()
    backend.invoke_command(1, 1, "OnOff", "On", {})
    assert backend.invoke_command(1, 1, "OnOff", "Off", {}) == {
        "ok": True,
        "status": "SUCCESS",
    }
    assert backend.read_attribute(1, 1, "OnOff", "OnOff") == {
        "ok": True,
        "value": False,
    }


def test_invoke_other_command_still_succeeds() -> None:
    backend = MockBackend()
    assert backend.invoke_command(1, 1, "LevelControl", "MoveToLevel", {"level": 50}) == {
        "ok": True,
        "status": "SUCCESS",
    }


def test_matter_backend_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        MatterBackend()  # type: ignore[abstract]
