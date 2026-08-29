"""SHALLOT Harness HTTP server — exposes the Pydantic AI agent for the PWA dashboard.

Streams real tool calls + text as SSE so the UI can render tool cards and HITL
approval gates (UX research 5.3–5.4). Stdlib only; no new dependencies.

Run:  uv run python -m shallot_harness.server
Env:  HARNESS_MODEL  (default ollama:ministral-3:8b-instruct-2512-q4_K_M)
      HARNESS_HOST  (default 0.0.0.0)
      HARNESS_PORT  (default 8000)
      HARNESS_DATA  (default ./harness_data)
"""

import asyncio
import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Serialize agent runs so Ollama (one generation at a time) is never backlogged by
# stacked browser requests — that backlog is what made the chat appear stuck.
RUN_LOCK = threading.Lock()
RUN_TIMEOUT = 45

import shallot_harness._otel_events_stub  # must precede pydantic_ai
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from shallot_harness.agent import create_agent
from shallot_harness.harness import Harness
from shallot_harness.stub_reasoner import StubReasoner

# pydantic-ai 0.8.1 has no native Ollama; route through Ollama's OpenAI-compatible /v1.
# Set OPENAI_BASE_URL=http://localhost:11434/v1 and OPENAI_API_KEY=ollama (any non-empty).
MODEL = os.environ.get("HARNESS_MODEL", "openai:ministral-3:8b-instruct-2512-q4_K_M")
DATA_DIR = os.environ.get("HARNESS_DATA", os.path.join(os.path.dirname(__file__), "..", "harness_data"))
os.makedirs(DATA_DIR, exist_ok=True)

_harness = Harness(
    "shallot",
    os.environ.get("HARNESS_REPO", os.getcwd()),
    os.path.join(DATA_DIR, "harness.db"),
    StubReasoner(),
)
_agent = create_agent(_harness, model=MODEL)


def _to_messages(msgs: list[dict]) -> list:
    out = []
    for m in msgs:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            out.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif role == "assistant":
            out.append(ModelResponse(parts=[TextPart(content=content)]))
    return out


def _extract_tools(result) -> list[dict]:
    calls: dict[str, dict] = {}
    results: dict[str, str] = {}
    for msg in result.all_messages():
        for p in msg.parts:
            if isinstance(p, ToolCallPart):
                calls[p.tool_call_id] = {
                    "id": p.tool_call_id,
                    "name": p.tool_name,
                    "args": _safe_json(p.args),
                }
            elif isinstance(p, ToolReturnPart):
                results[p.tool_call_id] = _truncate(str(p.content))
    tools = []
    for cid, c in calls.items():
        tools.append({**c, "result": results.get(cid, "")})
    return tools


def _safe_json(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)


def _truncate(s: str, n: int = 400) -> str:
    return s if len(s) <= n else s[:n] + "…"


def _pending_approvals() -> list[dict]:
    out = []
    for a in _harness._policy._approvals.pending():
        out.append({"action_id": str(a.action_id), "kind": a.kind, "target": a.target})
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, obj: dict) -> None:
        self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8"))
        self.wfile.flush()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, b'{"ok":true}')
        elif path == "/approvals":
            self._send(200, json.dumps({"approvals": _pending_approvals()}).encode("utf-8"))
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            payload = {}

        if path == "/chat":
            self._handle_chat(payload)
        elif path == "/approve":
            self._handle_approve(payload)
        else:
            self._send(404, b'{"error":"not found"}')

    def _handle_approve(self, payload):
        aid = payload.get("action_id")
        try:
            ok = _harness._policy.approve(uuid.UUID(aid))
        except Exception as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, json.dumps({"ok": ok, "approvals": _pending_approvals()}).encode("utf-8"))

    def _handle_chat(self, payload):
        messages = payload.get("messages", [])
        if not messages:
            self._send(400, b'{"error":"Missing messages"}')
            return
        history = _to_messages(messages[:-1])
        user_text = messages[-1].get("content", "")

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            with RUN_LOCK:
                result = asyncio.run(
                    asyncio.wait_for(
                        _agent.run(
                            user_text,
                            message_history=history,
                            model_settings={"max_tokens": 700},
                        ),
                        timeout=RUN_TIMEOUT,
                    )
                )
            tools = _extract_tools(result)
            for t in tools:
                self._sse({"tool_call": {"name": t["name"], "args": t["args"], "result": t["result"]}})
            text = result.output if isinstance(result.output, str) else str(result.output)
            for chunk in text.split(" "):
                self._sse({"token": chunk + " "})
            # surface any pending approvals raised during the run
            pending = _pending_approvals()
            if pending:
                self._sse({"approvals": pending})
            self._sse({"done": True, "model": MODEL})
        except (TimeoutError, asyncio.TimeoutError):
            self._sse({"token": "[timeout: svaret tog för lång tid — ställ en mer avgränsad fråga eller försök igen] "})
            self._sse({"done": True, "model": MODEL})
        except Exception as e:
            self._sse({"error": str(e)})

    def log_message(self, *args):
        pass


def main():
    host = os.environ.get("HARNESS_HOST", "0.0.0.0")
    port = int(os.environ.get("HARNESS_PORT", "8000"))
    print(f"SHALLOT Harness server on {host}:{port} (model {MODEL})")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
