#!/usr/bin/env bash
# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT
#
# Step-0 gate: prove qwen2.5:3b triggers a tool call via ollama-mcp-bridge.
set -euo pipefail

# Use the project venv so the bridge (and the MCP server subprocess it spawns)
# has access to the installed mcp SDK.
VENV="$(cd "$(dirname "$0")/.." && pwd)/.venv"

"$VENV/bin/ollama-mcp-bridge" \
  --config /tmp/toy-mcp-config.json \
  --ollama-url http://localhost:11434 \
  --port 8000 &
BRIDGE_PID=$!
trap 'kill $BRIDGE_PID 2>/dev/null || true' EXIT
sleep 5

echo "Asking the model to add 17 and 25..."
RESP=$(curl -fsS http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role":"user","content":"Use the add tool to add 17 and 25. Reply with just the number."}],
    "stream": false
  }')

echo "Raw response:"
echo "$RESP"
echo "$RESP" | grep -q "42" && echo "PASS: model tool-called, got 42" || { echo "FAIL: expected 42"; exit 1; }
