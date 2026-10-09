#!/usr/bin/env python3
"""Matter MCP chat command-line client.

Pure standard library. Talks to the ollama-mcp-bridge /api/chat endpoint over
HTTP so the local qwen2.5:3b model can call Matter MCP tools to operate devices.
Zero third-party dependencies for easy porting to i.MX93 Yocto.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

try:
    import readline  # noqa: F401  # enables arrow-key history / line editing
except ImportError:  # pragma: no cover - readline is optional on some platforms
    readline = None

DEFAULT_URL = "http://127.0.0.1:8000"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_TIMEOUT = 120
HELP = "Type a message to talk to your devices. Commands: /reset clear conversation, /clear clear screen, /health show status, /quit exit."


def get_health(url: str, timeout: float) -> dict:
    req = urllib.request.Request(f"{url}/health", method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_chat(url: str, model: str, messages: list, timeout: float) -> dict:
    body = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def print_tool_details(message: dict) -> None:
    tool_calls = message.get("tool_calls")
    if tool_calls:
        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "?")
            arguments = fn.get("arguments", {})
            print(f"  [tool] {name} args={arguments}")


def handle_turn(args: argparse.Namespace, messages: list, text: str) -> None:
    messages.append({"role": "user", "content": text})
    try:
        resp = post_chat(args.url, args.model, messages, args.timeout)
    except urllib.error.HTTPError as exc:
        print(f"Error: bridge returned HTTP {exc.code}")
        messages.pop()
        return
    except urllib.error.URLError as exc:
        print(f"Error: connection failed - {exc.reason}")
        messages.pop()
        return
    except json.JSONDecodeError:
        print("Error: response is not valid JSON")
        messages.pop()
        return

    message = resp.get("message")
    if not isinstance(message, dict):
        print("Error: response is missing the 'message' field")
        messages.pop()
        return

    print_tool_details(message)
    content = message.get("content", "")
    print(f"assistant> {content}")
    messages.append({"role": "assistant", "content": content})


def show_health(args: argparse.Namespace) -> None:
    try:
        health = get_health(args.url, args.timeout)
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        print(f"Error: could not fetch bridge status - {exc}")
        return
    status = health.get("status", "?")
    ollama_status = health.get("ollama_status", "?")
    tools = health.get("tools", "?")
    print(f"Bridge: {status} | Ollama: {ollama_status} | Tools: {tools}")


def clear_screen() -> None:
    # ANSI clear screen + move cursor home; works on Linux terminals.
    print("\033[2J\033[H", end="")


def main() -> int:
    parser = argparse.ArgumentParser(description="Matter MCP chat command-line client")
    parser.add_argument("--url", default=DEFAULT_URL, help="ollama-mcp-bridge address")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="request timeout (seconds)")
    args = parser.parse_args()

    try:
        health = get_health(args.url, args.timeout)
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        print(f"Error: cannot connect to bridge ({args.url}). Please run scripts/run_bridge.sh first.")
        return 1

    status = health.get("status", "?")
    ollama_status = health.get("ollama_status", "?")
    tools = health.get("tools", "?")
    print(f"Bridge: {status} | Ollama: {ollama_status} | Tools: {tools}")
    print(HELP)

    messages: list = []
    while True:
        try:
            text = input("you> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye")
            return 0
        if not text:
            continue
        if text in ("/quit", "/exit"):
            print("Bye")
            return 0
        if text == "/reset":
            messages.clear()
            print("Conversation reset")
            continue
        if text == "/clear":
            clear_screen()
            continue
        if text == "/health":
            show_health(args)
            continue
        if text.startswith("/"):
            print("Unknown command")
            continue
        handle_turn(args, messages, text)


if __name__ == "__main__":
    sys.exit(main())
