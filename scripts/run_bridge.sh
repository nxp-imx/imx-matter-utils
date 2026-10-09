#!/usr/bin/env bash
# Launch ollama-mcp-bridge with the Matter MCP server config.
#
# Configurable via environment variables:
#   OLLAMA_URL          Ollama server URL      (default http://localhost:11434)
#   BRIDGE_HOST         bridge listen host     (default 127.0.0.1)
#   BRIDGE_PORT         bridge listen port     (default 8000)
#   MAX_TOOL_ROUNDS     max tool-call rounds   (default 5)
#   MATTER_MCP_CONFIG_DIR  where mcp-config.json / system-prompt.txt live
#                       (default: /etc/matter-mcp when it exists, else the
#                        in-repo config/ dir for a git checkout)
#   OLLAMA_MCP_BRIDGE   path to the ollama-mcp-bridge executable
#                       (default: in-repo .venv/bin, else PATH lookup)
#
# Examples:
#   ./scripts/run_bridge.sh
#   OLLAMA_URL=http://10.52.9.94:8081 ./scripts/run_bridge.sh
#
# Note: the chat MODEL name is chosen by the client (e.g.
#   python3 scripts/chat_cli.py --model gemma4:26b), not by this script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Config dir: explicit env var wins, then the packaged /etc location, then the
# in-repo config/ dir so a plain git checkout still runs.
if [ -n "${MATTER_MCP_CONFIG_DIR:-}" ]; then
  CONFIG_DIR="${MATTER_MCP_CONFIG_DIR}"
elif [ -d /etc/matter-mcp ]; then
  CONFIG_DIR="/etc/matter-mcp"
else
  CONFIG_DIR="${REPO_ROOT}/config"
fi

# Bridge executable: explicit env var wins, then the in-repo venv, then PATH.
if [ -n "${OLLAMA_MCP_BRIDGE:-}" ]; then
  BRIDGE_BIN="${OLLAMA_MCP_BRIDGE}"
elif [ -x "${REPO_ROOT}/.venv/bin/ollama-mcp-bridge" ]; then
  BRIDGE_BIN="${REPO_ROOT}/.venv/bin/ollama-mcp-bridge"
else
  BRIDGE_BIN="ollama-mcp-bridge"
fi

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
BRIDGE_HOST="${BRIDGE_HOST:-127.0.0.1}"
BRIDGE_PORT="${BRIDGE_PORT:-8000}"
MAX_TOOL_ROUNDS="${MAX_TOOL_ROUNDS:-5}"

echo "Ollama URL: ${OLLAMA_URL}  |  bridge: ${BRIDGE_HOST}:${BRIDGE_PORT}  |  config: ${CONFIG_DIR}" >&2

exec "${BRIDGE_BIN}" \
  --config "${CONFIG_DIR}/mcp-config.json" \
  --ollama-url "${OLLAMA_URL}" \
  --system-prompt "$(cat "${CONFIG_DIR}/system-prompt.txt")" \
  --max-tool-rounds "${MAX_TOOL_ROUNDS}" \
  --host "${BRIDGE_HOST}" \
  --port "${BRIDGE_PORT}"
