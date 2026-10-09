#!/usr/bin/env bash
# Drive the 4 demo scenarios through the bridge. Requires run_bridge.sh running.
set -euo pipefail
URL=http://localhost:8000/api/chat

ask() {
  echo "=== $1 ==="
  curl -fsS "$URL" -H 'Content-Type: application/json' -d "{
    \"model\": \"qwen2.5:3b\",
    \"messages\": [{\"role\":\"user\",\"content\":\"$1\"}],
    \"stream\": false
  }"
  echo; echo
}

ask "What Matter devices are available?"
ask "Is the lab light on?"
ask "Turn off the lab light."
ask "What is the lab temperature?"
