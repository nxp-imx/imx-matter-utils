#!/usr/bin/env bash
# Copyright 2026 NXP
#
# SPDX-License-Identifier: MIT
#
# Install Ollama and pull the qwen2.5:3b model.
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Ollama already installed: $(ollama --version)"
fi

# Ensure the daemon is up (install script starts a systemd service on most distros).
if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Starting ollama serve in background..."
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  sleep 3
fi

echo "Pulling qwen2.5:3b (this may take a few minutes)..."
ollama pull qwen2.5:3b

echo "Done. Installed models:"
ollama list
