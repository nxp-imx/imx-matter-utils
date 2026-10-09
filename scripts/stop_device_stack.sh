#!/usr/bin/env bash
#
# Stop the real-device Matter stack started by start_device_stack.sh.
#
# Kills the ollama-mcp-bridge, the chip-tool WebSocket server, and the
# chip-lighting-app by their real process, closes the tmux session, and
# removes the temporary storage directories.
#
# Env vars (all optional, must match start_device_stack.sh if overridden):
#   SESSION   tmux session name          (default matter)
#   KVS       chip-lighting-app storage  (default /tmp/chip_lighting_kvs)
#   STORE     chip-tool storage dir      (default /tmp/chiptool_store)
set -euo pipefail

SESSION="${SESSION:-matter}"
KVS="${KVS:-/tmp/chip_lighting_kvs}"
STORE="${STORE:-/tmp/chiptool_store}"

# Kill the bridge by scanning cmdline (never pkill -f: it self-matches).
for p in $(ls /proc 2>/dev/null | grep -E '^[0-9]+$'); do
  [ "$p" = "$$" ] && continue
  c=$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null || true)
  case "$c" in
    *ollama-mcp-bridge*) echo "kill bridge $p"; kill -9 "$p" 2>/dev/null || true;;
  esac
done

# Kill chip-lighting-app / chip-tool by their real exe symlink.
for p in $(ls /proc 2>/dev/null | grep -E '^[0-9]+$'); do
  e=$(readlink "/proc/$p/exe" 2>/dev/null || true)
  case "$e" in
    */chip-lighting-app|*/chip-tool) echo "kill $e ($p)"; kill -9 "$p" 2>/dev/null || true;;
  esac
done

tmux kill-session -t "${SESSION}" 2>/dev/null || true
rm -rf "${KVS}" "${STORE}"

echo "stopped session '${SESSION}', cleaned ${KVS} ${STORE}"
