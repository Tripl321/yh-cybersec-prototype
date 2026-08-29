"""SHALLOT Harness HTTP server — exposes the Agno agent for the PWA dashboard.

Streams tool calls + text as SSE so the UI can render tool cards and HITL
approval gates. Stdlib only; no new dependencies.

Run:  uv run python -m shallot_harness.server
Env:  HARNESS_MODEL  (default ollama:qwen3:14b)
      HARNESS_HOST  (default 0.0.0.0)
      HARNESS_PORT  (default 7777 — Agno AgentOS standard, 8000 upptaget av demo/system)
      HARNESS_DATA  (default ./harness_data)
"""

import json
import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

RUN_LOCK = threading.Lock()
RUN_TIMEOUT = 45

from shallot_harness.agent import create_agent
from shallot_harness.harness import Harness
from shallot_harness.stub_reasoner import StubReasoner

MODEL = os.environ.get("HARNESS_MODEL", "ollama:qwen3:14b")
DATA_DIR = os.environ.get("HARNESS_DATA", os.path.join(os.path.dirname(__file__), "..", "harness_data"))
os.makedirs(DATA_DIR, exist_ok=True)

_harness = Harness(
    "shallot",
    os.environ.get("HARNESS_REPO", os.getcwd()),
    os.path.join(DATA_DIR, "harness.db"),
    StubReasoner(),
)
_agent = create_agent(_harness, model=MODEL)


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
        user_text = messages[-1].get("content", "")

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            with RUN_LOCK:
                # Agno run is sync; previous async wrapper not needed
                result = _agent.run(user_text)
                # RunOutput has .content or .get_content_as_string()
                text = ""
                if hasattr(result, "content"):
                    text = result.content or ""
                elif hasattr(result, "get_content_as_string"):
                    text = result.get_content_as_string() or ""
                else:
                    text = str(result)

                # Stream tokens as SSE for PWA compatibility
                for chunk in text.split(" "):
                    self._sse({"token": chunk + " "})
                pending = _pending_approvals()
                if pending:
                    self._sse({"approvals": pending})
                self._sse({"done": True, "model": MODEL})
        except Exception as e:
            self._sse({"error": str(e)})

    def log_message(self, *args):
        pass


def main():
    host = os.environ.get("HARNESS_HOST", "0.0.0.0")
    port = int(os.environ.get("HARNESS_PORT", "7777"))
    print(f"SHALLOT Harness server on {host}:{port} (model {MODEL})")
    try:
        ThreadingHTTPServer((host, port), Handler).serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Port {port} upptagen — prova HARNESS_PORT=7777 eller 8001 (demo kör på 8000): {e}")
        raise


if __name__ == "__main__":
    main()
