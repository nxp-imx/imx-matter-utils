# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

"""Uniform MCP tool error codes and helper.

All four Matter MCP tools return structured JSON. On failure they return the
uniform shape ``{"ok": False, "error": "<code>"}`` using this fixed set of
error-code string constants. The string VALUES are the wire contract.
"""

ERR_UNKNOWN_NODE = "unknown_node"
ERR_UNKNOWN_ENDPOINT = "unknown_endpoint"
ERR_UNSUPPORTED_CLUSTER = "unsupported_cluster"
ERR_UNSUPPORTED_ATTRIBUTE = "unsupported_attribute"
ERR_UNSUPPORTED_COMMAND = "unsupported_command"
ERR_CHIP_ERROR = "chip_error"


def error(code: str) -> dict:
    """Build the uniform MCP tool error response."""
    return {"ok": False, "error": code}
