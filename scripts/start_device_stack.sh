#!/usr/bin/env bash
#
# Start the full REAL-DEVICE Matter stack for end-to-end chat testing.
#
# Brings up, each in its own tmux window of session "$SESSION":
#   1. chip-lighting-app  (the simulated Matter light, node 1)
#   2. chip-tool pairing onnetwork 1   (commission the light)
#   3. chip-tool interactive server    (WebSocket backend on :9002)
#   4. ollama-mcp-bridge               (HTTP /api/chat on :8000)
#
# This is REAL-DEVICE only (config/mcp-config.json uses the chiptool backend).
# No mock is involved.
#
# Env vars (all optional):
#   OLLAMA_URL    Ollama server for the bridge   (default http://localhost:11434)
#   SESSION       tmux session name              (default matter)
#   DISCRIMINATOR chip-lighting-app discriminator (default 3840)
#   PASSCODE      commissioning passcode          (default 20202021)
#   KVS           chip-lighting-app storage       (default /tmp/chip_lighting_kvs)
#   STORE         chip-tool storage directory     (default /tmp/chiptool_store)
#   WS_PORT       chip-tool WebSocket port        (default 9002)
#   LOGDIR        directory for stack logs        (default /tmp)
#
# Example (i.MX93 board, remote Ollama with gemma4:26b):
#   OLLAMA_URL=http://10.52.9.94:8081 ./scripts/start_device_stack.sh
#
# Then drive it:
#   python3 scripts/chat_cli.py --url http://127.0.0.1:8000 --model gemma4:26b
#
# Stop everything:
#   ./scripts/stop_device_stack.sh
set -euo pipefail

cd "$(dirname "$0")/.."

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
SESSION="${SESSION:-matter}"
DISCRIMINATOR="${DISCRIMINATOR:-3840}"
PASSCODE="${PASSCODE:-20202021}"
KVS="${KVS:-/tmp/chip_lighting_kvs}"
STORE="${STORE:-/tmp/chiptool_store}"
WS_PORT="${WS_PORT:-9002}"
LOGDIR="${LOGDIR:-/tmp}"

echo "Session: ${SESSION} | Ollama: ${OLLAMA_URL} | WS port: ${WS_PORT}"

# chip-tool refuses to start if the storage directory does not already exist.
rm -rf "${KVS}" "${STORE}"
mkdir -p "${STORE}"

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" \
  "/usr/bin/chip-lighting-app --discriminator ${DISCRIMINATOR} --passcode ${PASSCODE} --KVS ${KVS} > ${LOGDIR}/matter_lighting.log 2>&1"
echo "[1/4] chip-lighting-app starting (log: ${LOGDIR}/matter_lighting.log)"
sleep 5

tmux new-window -t "${SESSION}" -n pair \
  "chip-tool pairing onnetwork 1 ${PASSCODE} --storage-directory ${STORE} > ${LOGDIR}/matter_pair.log 2>&1"
echo "[2/4] commissioning node 1 ..."
sleep 25
if grep -q "Commissioning complete for node ID 0x0000000000000001: success" "${LOGDIR}/matter_pair.log"; then
  echo "      commissioning OK"
else
  echo "      commissioning may have failed, see ${LOGDIR}/matter_pair.log" >&2
fi

tmux new-window -t "${SESSION}" -n ws \
  "chip-tool interactive server --port ${WS_PORT} --storage-directory ${STORE} > ${LOGDIR}/matter_ws.log 2>&1"
echo "[3/4] chip-tool WebSocket server starting on :${WS_PORT}"
sleep 4

tmux new-window -t "${SESSION}" -n bridge \
  "cd $(pwd) && OLLAMA_URL=${OLLAMA_URL} ./scripts/run_bridge.sh > ${LOGDIR}/matter_bridge.log 2>&1"
echo "[4/4] ollama-mcp-bridge starting on :8000"

echo
echo "Waiting for bridge health ..."
for i in $(seq 1 15); do
  if curl -s --max-time 3 http://127.0.0.1:8000/health | grep -q '"tools":4'; then
    echo "READY: $(curl -s http://127.0.0.1:8000/health)"
    echo
    echo "Drive it with:"
    echo "  python3 scripts/chat_cli.py --url http://127.0.0.1:8000 --model <model>"
    exit 0
  fi
  sleep 2
done
echo "Bridge not healthy yet; check ${LOGDIR}/matter_bridge.log" >&2
exit 1
