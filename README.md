# Matter MCP Server

A Python MCP server that exposes Matter device tools to a local LLM via
[ollama-mcp-bridge](https://github.com/patruff/ollama-mcp-bridge). Two
backends are supported: a real backend driving `chip-tool interactive
server` over WebSocket (default), and an in-memory mock backend for
development without hardware (`MATTER_MCP_BACKEND=mock`).

## Development

Install the package in editable mode with development dependencies:

```bash
.venv/bin/pip install -e '.[dev]'
```

Run the tests:

```bash
.venv/bin/pytest
```
