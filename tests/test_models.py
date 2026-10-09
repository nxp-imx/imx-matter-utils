# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT

from matter_mcp import models


def test_error_code_constants():
    assert models.ERR_UNKNOWN_NODE == "unknown_node"
    assert models.ERR_UNKNOWN_ENDPOINT == "unknown_endpoint"
    assert models.ERR_UNSUPPORTED_CLUSTER == "unsupported_cluster"
    assert models.ERR_UNSUPPORTED_ATTRIBUTE == "unsupported_attribute"
    assert models.ERR_UNSUPPORTED_COMMAND == "unsupported_command"


def test_error_helper_with_constant():
    assert models.error(models.ERR_UNKNOWN_NODE) == {"ok": False, "error": "unknown_node"}


def test_error_helper_is_code_agnostic():
    assert models.error("anything") == {"ok": False, "error": "anything"}


def test_err_chip_error_constant():
    from matter_mcp import models
    assert models.ERR_CHIP_ERROR == "chip_error"
    assert models.error(models.ERR_CHIP_ERROR) == {"ok": False, "error": "chip_error"}
