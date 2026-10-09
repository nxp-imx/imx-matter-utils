# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

import json
import pytest
from matter_mcp.chip_ws_adapter import ChipWsAdapter


class _FakeConn:
    """Records sent strings, returns queued recv payloads (JSON strings)."""
    def __init__(self, recv_payloads):
        self._recv = list(recv_payloads)
        self.sent = []
        self.closed = False
        self.raise_on_send = False

    def send(self, s):
        if self.raise_on_send:
            raise ConnectionError("socket closed")
        self.sent.append(s)

    def recv(self):
        return self._recv.pop(0)

    def close(self):
        self.closed = True


def _factory(conns):
    """Return a connect_fn that yields the given fake conns in order."""
    it = iter(conns)

    def connect_fn(url, timeout=None):
        return next(it)

    return connect_fn


def test_send_command_returns_parsed_dict():
    conn = _FakeConn([json.dumps({"results": [], "logs": []})])
    a = ChipWsAdapter("ws://x", connect_fn=_factory([conn]))
    a.connect()
    out = a.send_command("onoff on 1 1")
    assert out == {"results": [], "logs": []}
    assert conn.sent == ["onoff on 1 1"]


def test_send_command_reconnects_once_on_failure():
    # first conn fails on send; adapter reconnects with a fresh conn and succeeds
    bad = _FakeConn([])
    bad.raise_on_send = True
    good = _FakeConn([json.dumps({"results": [{"value": True}]})])
    a = ChipWsAdapter("ws://x", connect_fn=_factory([bad, good]))
    a.connect()
    out = a.send_command("onoff read on-off 1 1")
    assert out == {"results": [{"value": True}]}
    assert good.sent == ["onoff read on-off 1 1"]


def test_send_command_raises_after_second_failure():
    bad1 = _FakeConn([]); bad1.raise_on_send = True
    bad2 = _FakeConn([]); bad2.raise_on_send = True
    a = ChipWsAdapter("ws://x", connect_fn=_factory([bad1, bad2]))
    a.connect()
    with pytest.raises(Exception):
        a.send_command("onoff on 1 1")


def test_close_closes_connection():
    conn = _FakeConn([])
    a = ChipWsAdapter("ws://x", connect_fn=_factory([conn]))
    a.connect()
    a.close()
    assert conn.closed is True
