"""MCP server interface for SHALLOT Harness."""

from mcp.server.fastmcp import FastMCP

from shallot_harness.harness import Harness

mcp = FastMCP("shallot-harness")

_harness: Harness | None = None


def init_harness(harness: Harness) -> None:
    global _harness
    _harness = harness


def _harness_or_error() -> Harness:
    if _harness is None:
        raise RuntimeError("Harness not initialized — call init_harness first")
    return _harness


@mcp.tool()
def get_project_state() -> str:
    """Get current SHALLOT project state."""
    h = _harness_or_error()
    state = h.current_state()
    if state is None:
        return "No state recorded yet."
    return (
        f"Project: {state.project_id}\n"
        f"Issue: #{state.current_issue}\n"
        f"Next action: {state.next_action}\n"
        f"Verification: {state.verification_criterion}"
    )


@mcp.tool()
def run_harness(goal: str = "Continue SHALLOT prototype development") -> str:
    """Run one harness lifecycle: context → reason → gate → record."""
    h = _harness_or_error()
    result = h.run(goal=goal)
    state = result["state"]
    verdict = result["verdict"]
    return (
        f"Next action: {state.next_action}\n"
        f"Reasoning: {state.verification_criterion}\n"
        f"Allowed: {verdict.allowed}\n"
        f"Reason: {verdict.reason}"
    )


@mcp.tool()
def get_events(limit: int = 10) -> str:
    """Get recent project events."""
    h = _harness_or_error()
    events = h._ledger.events(h.project_id)
    lines = []
    for e in events[-limit:]:
        prov = f" by {e.provenance.actor}" if e.provenance else ""
        lines.append(f"[{e.occurred_at}] {e.payload.next_action}{prov}")
    return "\n".join(lines) if lines else "No events."


@mcp.tool()
def approve_action(action_id: str) -> str:
    """Approve a pending HITL action."""
    from uuid import UUID

    h = _harness_or_error()
    ok = h._policy.approve(UUID(action_id))
    return "Approved." if ok else "Action not found or already processed."


@mcp.tool()
def search_memory(query: str = "", namespace: str = "") -> str:
    """Search structured memory."""
    h = _harness_or_error()
    ns = namespace or None
    memories = h._memory.query(namespace=ns)
    if query:
        memories = [m for m in memories if query.lower() in m.content.lower()]
    if not memories:
        return "No matching memories."
    lines = [f"[{m.namespace}] {m.content}" for m in memories]
    return "\n".join(lines)
