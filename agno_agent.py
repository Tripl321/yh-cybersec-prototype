"""
SHALLOT Harness — project management agent (Agno MVP, ADR 0010 / ticket #82).

ONE local-first Agno agent for project management, development, research,
cybersecurity work, and physical builds of the SHALLOT project. Distinct from
Cub (operational OT agent). No cloud: local Ollama, local SqliteDb, agentic
memory, HITL approval on sensitive tools, egress-deny + provenance hooks.

Build-ref: docs/architecture/agno-mvp-build.md
ADR:       docs/adr/0010-standalone-shallot-harness.md

Install:  uv pip install -U "agno[os]" ollama
Model:    local Ollama (set SHALLOT_MODEL; default ministral-3:8b, ADR 0010).
Run:      python agno_agent.py            # CLI (default, D1 HITL terminal prompt)
          SHALLOT_SERVE=1 python agno_agent.py   # AgentOS on 127.0.0.1:7777 (D2, AG-UI)
Env:      SHALLOT_MODEL      default model (ministral-3:8b)
          SHALLOT_DB_URL     postgres+psycopg://... -> PostgresDb (D5); else SqliteDb
          SHALLOT_GIT_MCP_URL / SHALLOT_GIT_MCP_CMD  opt-in MCP git-server (D7)
          VISION_MODEL       reserved for a future vision agent (qwen3-vl:8b, D3)
"""

import os
import shlex
import subprocess
from pathlib import Path

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.ollama import Ollama
from agno.tools import tool

from cub.hooks import provenance_pre_hook, provenance_post_hook

REPO = Path(__file__).resolve().parent
Path("tmp").mkdir(exist_ok=True)

MODEL_ID = os.getenv("SHALLOT_MODEL", "ministral-3:8b")  # local Ollama (ADR 0010)

SYSTEM_PROMPT = """\
You are the SHALLOT Harness: a standalone personal agent for project management,
development, research, cybersecurity work, and physical builds of the SHALLOT
project (secure-by-design OT access control with phishing-resistant FIDO2 hardware).

Operating principles:
- Local-first: all inference runs on local Ollama. Do not contact external
  services; egress tools are blocked by design.
- Ground decisions in the project's own docs (ADRs, specs, dev log) and the
  frameworks NIST CSF 2.0, NIST SP 800-53r5, MITRE ATT&CK, CIS Controls v8.
- Use your tools to read project state, history, and budget before answering.
- Sensitive actions (approve_action, run_harness) require human confirmation
  (HITL) — pause and let the human decide, never auto-execute them.
- Model output is a proposal, never canonical fact or active procedure.
- Respond in Swedish or English as the user writes.
"""


def _read(path: Path, limit: int = 6000) -> str:
    if not path.exists():
        return f"[missing: {path.name}]"
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit]


# --- D8: run_harness safety allowlist (wayfinder ticket D8, resolved) ---
# Deny-by-default. Only test/build/lint + read-only repo ops may run. The
# cub.hooks egress-deny is name-based and does NOT inspect shell content, so
# the allowlist is enforced here, in-tool, with shell=False.
RUN_ALLOWLIST_FIRST = {
    "pytest", "python", "npm", "ruff", "mypy", "node",
    "ls", "cat", "head", "tail", "grep",
}
RUN_DENY_FIRST = {
    "sudo", "su", "rm", "dd", "mkfs", "chmod", "chown",
    "curl", "wget", "ssh", "scp", "nc", "telnet", "ping", "ftp", "rsync",
}
RUN_SHELL_METACHARS = set(";|&`$><\n")


def _validate_run_command(command: str) -> str:
    """Return '' if allowed, else a human-readable denial reason (D8)."""
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"cannot parse command: {e}"
    if not parts:
        return "empty command"
    first = parts[0]
    if first in RUN_DENY_FIRST:
        return f"'{first}' is denied (network/privileged/destructive)"
    if first not in RUN_ALLOWLIST_FIRST:
        return f"'{first}' not in allowlist (deny-by-default)"
    if first == "npm" and len(parts) > 1 and parts[1] not in {"test", "run"}:
        return "npm only allowed for 'test' / 'run' (build|lint)"
    if first == "python" and len(parts) > 1 and parts[1] in {"-c", "-i"}:
        return "python arbitrary exec (-c/-i) denied"
    if any(ch in RUN_SHELL_METACHARS for ch in command):
        return "shell metacharacters not allowed"
    for arg in parts[1:]:
        if arg.startswith("/") and not arg.startswith(str(REPO)):
            return f"path escapes repo root: {arg}"
        if ".ssh" in arg or arg.startswith("/etc"):
            return f"system path denied: {arg}"
    return ""


@tool(pre_hook=provenance_pre_hook, post_hook=provenance_post_hook)
def get_project_state() -> str:
    """Read current SHALLOT project state from ADRs, specs, and the dev log."""
    sources = [
        REPO / "docs" / "DEVELOPMENT-LOG.md",
        REPO / "docs" / "architecture" / "shallot-spec.md",
        REPO / "docs" / "adr" / "0010-standalone-shallot-harness.md",
        REPO / "docs" / "adr" / "0003-access-roles-mama-bear-cub.md",
        REPO / "docs" / "grc" / "REGISTRY.md",
        REPO / "docs" / "specs" / "prototype-scope.md",
    ]
    out = ["# SHALLOT project state"]
    for s in sources:
        out.append(f"\n## {s.relative_to(REPO)}\n{_read(s)}")
    return "\n".join(out)


@tool(pre_hook=provenance_pre_hook, post_hook=provenance_post_hook)
def get_event_history() -> str:
    """Return the development log (chronology of what was built and decided)."""
    return _read(REPO / "docs" / "DEVELOPMENT-LOG.md", limit=8000)


@tool(pre_hook=provenance_pre_hook, post_hook=provenance_post_hook)
def get_budget_status() -> str:
    """Report the SHALLOT MVP budget and timeline from CONTEXT.md."""
    ctx = _read(REPO / "CONTEXT.md")
    lines = [ln for ln in ctx.splitlines() if "Budget" in ln or "Tid" in ln or "veck" in ln]
    return "Budget status (from CONTEXT.md):\n" + ("\n".join(lines) or "Budget line not found.")


@tool(requires_confirmation=True, pre_hook=provenance_pre_hook, post_hook=provenance_post_hook)
def approve_action(action: str) -> str:
    """Approve a sensitive action (HITL). Pauses for human confirmation.

    Args:
        action: The action to approve, e.g. 'promote runbook update #12'.
    """
    return f"Approved by human: {action}"


@tool(requires_confirmation=True, pre_hook=provenance_pre_hook, post_hook=provenance_post_hook)
def run_harness(command: str) -> str:
    """Run a project command inside the repo (HITL). Allowlist-gated (D8): tests/build/lint + read-only repo ops, deny-by-default, no egress.

    Args:
        command: Command to run within the SHALLOT repo root (first token must be allowlisted).
    """
    reason = _validate_run_command(command)
    if reason:
        return f"DENIED by run_harness allowlist: {reason}"
    try:
        result = subprocess.run(
            shlex.split(command),
            shell=False,
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "Command timed out after 120s."
    return f"rc={result.returncode}\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"


# --- D5 seam: memory backend (SqliteDb MVP <-> PostgresDb post-MVP) ---
def get_db():
    """Return the agent db. MVP: SqliteDb. Post-MVP: PostgresDb when SHALLOT_DB_URL is set.
    Agentic memory + HITL approvals persist in this db; swapping is non-breaking (D5)."""
    db_url = os.getenv("SHALLOT_DB_URL")
    if db_url:
        from agno.db.postgres import PostgresDb

        return PostgresDb(db_url=db_url)
    return SqliteDb(db_file="tmp/agents.db")


# --- D7 seam: opt-in MCP git-server (project management) ---
def _git_tools():
    """Return MCP git tools if a git MCP server is configured (D7). Read-only by posture.
    Set SHALLOT_GIT_MCP_URL (streamable-http) or SHALLOT_GIT_MCP_CMD (stdio command)."""
    from agno.tools.mcp import MCPTools

    url = os.getenv("SHALLOT_GIT_MCP_URL")
    if url:
        return [MCPTools(transport="streamable-http", url=url)]
    cmd = os.getenv("SHALLOT_GIT_MCP_CMD")
    if cmd:
        return [MCPTools(command=cmd)]
    return []


shallot = Agent(
    name="SHALLOT",
    model=Ollama(id=MODEL_ID),
    instructions=SYSTEM_PROMPT,
    tools=[get_project_state, get_event_history, get_budget_status, approve_action, run_harness]
    + _git_tools(),
    db=get_db(),
    enable_agentic_memory=True,  # supplies search_memory / add_memory tools
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)


if __name__ == "__main__":
    # MVP default: interactive local CLI. Sensitive tools pause for HITL confirmation (D1).
    if os.getenv("SHALLOT_SERVE") == "1":
        # Opt-in AgentOS serve on localhost:7777 (D2). Connect stock agent-ui via AG-UI.
        # NOTE: serve() signature may vary by installed agno[os] version; adjust if needed.
        from agno.os import AgentOS

        agent_os = AgentOS(agents=[shallot], db=get_db())
        agent_os.serve(host="127.0.0.1", port=7777)
    else:
        shallot.cli_app()
