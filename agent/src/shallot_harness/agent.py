"""Agno agent — SHALLOT project management brain."""

from __future__ import annotations

import os

from agno.agent import Agent
from agno.tools.decorator import tool
from agno.tools.duckduckgo import DuckDuckGoTools

from shallot_harness.harness import Harness

SYSTEM_PROMPT = """You are SHALLOT Harness — a project management agent for the SHALLOT OT access control prototype (YH cybersecurity project).

Fixed architecture:
- PAW: Feather RP2350 + E-ink + Core1262-HF LoRa + LiPo
- FIDO Key: ESP32-S3-Nano running PicoFIDO (USB-serial signing)
- Field Node: Pico 2 W + Core1262-HF LoRa + relay
- Mama Bear: Arduino UNO Q (air-gapped provisioning root)

Communication:
- Beacon: Field Node → PAW (plaintext LoRa, 13 bytes)
- Auth request: PAW → Field Node (signed LoRa, 41 bytes, HMAC-SHA256)
- Nonce: 32-bit challenge from Field Node, one-time use
- Epoch-key: rolling HMAC secret synced via Mama Bear USB-serial

Rules:
- Check current state before suggesting actions
- Prefer acting on context you can fetch over asking the user
- Record every action with provenance
- Sensitive operations require human approval — return the pending approval
- Stay within the €20/month cloud budget
- Prefer local Ollama inference over cloud providers

Hardware bring-up order:
1. Power from USB first. Add LiPo only after USB bring-up.
2. Check resistance to ground before power; measure rails before inserting the radio.
3. Attach a matched 868 MHz antenna before SX1262 transmission.
4. Bring up one interface at a time: power → SPI → radio standby → RX/TX → peripherals.
5. Unknown pinout means blocker, not a guessed wire.

Security verification checklist:
- valid auth grants access
- invalid HMAC rejects
- reused nonce/counter rejects
- expired epoch rejects
- RSSI below threshold rejects
- heartbeat timeout returns relay OFF
- reboot starts relay OFF

"""

DEFAULT_MODEL = "ollama:qwen3:14b"
DEFAULT_VISION_MODEL = "ollama:qwen3-vl:8b"


def create_agent(harness: Harness, model: str | None = None) -> Agent:
    """Create an Agno agent with tools bound to a harness instance."""

    @tool
    def get_project_state() -> str:
        """Get the current SHALLOT project state — next action, verification criterion, issue."""
        state = harness.current_state()
        if state is None:
            return "No state recorded yet. Run the harness to initialize."
        return (
            f"Project: {state.project_id}\n"
            f"Current issue: #{state.current_issue}\n"
            f"Next action: {state.next_action}\n"
            f"Verification: {state.verification_criterion}"
        )

    @tool
    def get_event_history(limit: int = 10) -> str:
        """Get recent project events with timestamps and provenance."""
        events = harness._ledger.events(harness.project_id)
        if not events:
            return "No events recorded."
        lines = []
        for e in events[-limit:]:
            prov = f" by {e.provenance.actor}" if e.provenance else ""
            lines.append(f"[{e.occurred_at}] {e.payload.next_action}{prov}")
        return "\n".join(lines)

    @tool
    def run_harness(goal: str) -> str:
        """Run one harness lifecycle: read context, reason, gate, record. Returns the next action and verdict."""
        result = harness.run(goal=goal)
        state = result["state"]
        verdict = result["verdict"]
        return (
            f"Next action: {state.next_action}\n"
            f"Reasoning: {state.verification_criterion}\n"
            f"Allowed: {verdict.allowed}\n"
            f"Reason: {verdict.reason}"
        )

    @tool
    def search_memory(query: str = "", namespace: str = "") -> str:
        """Search structured memory. Filter by namespace (working, episodic, semantic, procedural) or query content."""
        ns = namespace or None
        memories = harness._memory.query(namespace=ns)
        if query:
            memories = [m for m in memories if query.lower() in m.content.lower()]
        if not memories:
            return "No matching memories."
        lines = [f"[{m.namespace}/{m.scope}] {m.content}" for m in memories]
        return "\n".join(lines)

    @tool
    def add_memory(content: str = "", namespace: str = "episodic", scope: str = "workspace:shallot") -> str:
        """Add a new memory entry. Use for facts, decisions, or observations worth remembering."""
        from shallot_harness.memory import Memory

        text = (content or "").strip()
        if not text:
            return "To store memory, I need the content to remember."

        if not harness.request_approval("memory.write", f"memory:{scope}", {"content": text, "namespace": namespace}):
            return "Memory pending approval. Use approve_action to approve before it is stored."
        m = Memory.create(namespace=namespace, scope=scope, content=text)
        harness._memory.add(m)
        return f"Memory stored: {m.memory_id} ({m.namespace}/{m.scope})"

    @tool
    def approve_action(action_id: str) -> str:
        """Approve a pending HITL action by its ID."""
        from uuid import UUID

        try:
            ok = harness._policy.approve(UUID(action_id))
        except (ValueError, TypeError):
            return f"Invalid action_id: {action_id!r}."
        return "Approved." if ok else "Action not found or already processed."

    @tool
    def get_budget_status() -> str:
        """Check remaining cloud budget for this month (€20 limit)."""
        remaining = harness._policy._budget.remaining()
        return f"Budget remaining: €{remaining:.2f} / €20.00"

    @tool
    def read_file(path: str) -> str:
        """Read a text file from the project repo. Use relative paths from the repo root."""
        base = harness._repo_path or os.getcwd()
        target = os.path.join(base, path)
        target = os.path.normpath(target)
        if not target.startswith(os.path.normpath(base)):
            return "Error: path escapes repo root"
        if not os.path.exists(target):
            return f"File not found: {path}"
        if os.path.isdir(target):
            return f"Error: {path} is a directory, not a file"
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
        except Exception as exc:
            return f"Error reading {path}: {exc}"
        if len(data) > 12000:
            data = data[:12000] + "\n... [truncated]"
        return data

    @tool
    def list_files(pattern: str = "**/*") -> str:
        """List files in the project repo matching a glob pattern (default: all files)."""
        import glob

        base = harness._repo_path or os.getcwd()
        matches = glob.glob(os.path.join(base, pattern), recursive=True)
        files = [os.path.relpath(m, base) for m in matches if os.path.isfile(m)]
        if not files:
            return "No files found."
        return "\n".join(sorted(files)[:50])

    @tool
    def search_files(query: str) -> str:
        """Search for files in the project by filename (case-insensitive substring match)."""
        base = harness._repo_path or os.getcwd()
        matches = []
        for root, dirs, files in os.walk(base):
            for f in files:
                if query.lower() in f.lower():
                    matches.append(os.path.relpath(os.path.join(root, f), base))
        if not matches:
            return f"No files matching '{query}' found."
        return "\n".join(sorted(matches)[:20])

    agent = Agent(
        id="shallot",
        name="SHALLOT Harness",
        model=model or DEFAULT_MODEL,
        instructions=SYSTEM_PROMPT,
        tools=[
            get_project_state,
            get_event_history,
            run_harness,
            search_memory,
            add_memory,
            approve_action,
            get_budget_status,
            read_file,
            list_files,
            search_files,
            DuckDuckGoTools(),
        ],
        markdown=True,
    )
    return agent
