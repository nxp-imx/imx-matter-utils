# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

"""Synchronous WebSocket transport to chip-tool interactive server.

Single connection, strict request-response: send one command string, receive
one JSON frame, return the decoded dict. No business parsing (that is
response_parser's job). One reconnect retry on a broken send/recv, then raise.
"""

from __future__ import annotations

import json
import logging

import websocket  # websocket-client (synchronous)

log = logging.getLogger(__name__)


class ChipWsAdapter:
    def __init__(self, url: str, timeout: float = 30.0, connect_fn=None) -> None:
        self._url = url
        self._timeout = timeout
        # connect_fn is a seam for tests; production uses websocket.create_connection.
        self._connect_fn = connect_fn or websocket.create_connection
        self._conn = None

    def connect(self) -> None:
        """Open the WebSocket connection. Raises on failure."""
        self._conn = self._connect_fn(self._url, timeout=self._timeout)

    def _reconnect(self) -> None:
        try:
            if self._conn is not None:
                self._conn.close()
        except Exception:
            pass
        self._conn = self._connect_fn(self._url, timeout=self._timeout)

    def send_command(self, cmd: str) -> dict:
        """Send a command string, return the decoded JSON response dict.

        On a transport error, reconnect once and retry. If the retry also
        fails, the exception propagates (the backend converts it to chip_error).
        """
        try:
            return self._roundtrip(cmd)
        except Exception as exc:
            log.warning("chip-tool WS roundtrip failed (%s); reconnecting once", exc)
            self._reconnect()
            return self._roundtrip(cmd)

    def send_command_probe(self, cmd: str, timeout: float) -> dict:
        """Send a command with a short per-call recv timeout and NO reconnect
        retry. Used by discovery probing so an unreachable node fails fast
        (one short timeout) instead of the full connect timeout + reconnect.
        The connection's recv timeout is restored afterward.
        """
        prev = None
        try:
            if self._conn is not None:
                prev = self._timeout
                self._conn.settimeout(timeout)
            return self._roundtrip(cmd)
        finally:
            if self._conn is not None and prev is not None:
                try:
                    self._conn.settimeout(prev)
                except Exception:
                    pass

    def _roundtrip(self, cmd: str) -> dict:
        self._conn.send(cmd)
        raw = self._conn.recv()
        return json.loads(raw)

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None
