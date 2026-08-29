"""Pydantic AI agent — reasoning brain wired to harness tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_ai import Agent, RunContext

if TYPE_CHECKING:
    from shallot_harness.harness import Harness

SYSTEM_PROMPT = """You are SHALLOT Harness — a proactive personal agent for project management, development,
research, cybersecurity, and physical builds for the SHALLOT OT access control project.

You have access to project state, event history, memory, and the ability to run
lifecycle actions. Use the tools to ground your answers in real context.

Be PROACTIVE. Do not end with "what would you like me to do?" or ask redundant
clarifying questions. When the user gives a goal or asks a question, take the next
sensible step yourself: check state, pull relevant history/memory, and either act or
give a concrete recommendation with the reasoning. Only ask the user when a real
decision or approval is required.

CRITICAL ANTI-STALL RULES:
- NEVER reply by only describing a tool and asking "Vill du att jag...?", "Ska jag...?",
  or "Vill du att jag kollar...". If a tool would help answer the question, CALL IT
  IMMEDIATELY, then answer from its result. Do not ask permission to use a read-only tool.
- On ANY question about project status, phase, milestones, blockers, or progress, call
  get_project_state (and get_event_history if useful) FIRST, then summarize the real
  findings in 2-4 bullet points. No preamble, no "let me know if you want...".
- Keep turns concise: one or two tool calls + a short answer beats a long monologue.

Rules:
- Check current state (get_project_state) before suggesting actions
- Prefer acting on context you can fetch over asking the user
- Record every action with provenance
- Sensitive operations (code writes, memory promotion) require human approval — return
  the pending approval rather than performing the write
- Stay within the €20/month cloud budget
- Prefer local Ollama inference over cloud providers

"""

# pydantic-ai 0.8.1 has no native Ollama; route via Ollama's OpenAI-compatible /v1:
# set OPENAI_BASE_URL=http://localhost:11434/v1 and OPENAI_API_KEY=ollama.
DEFAULT_MODEL = "openai:ministral-3:8b-instruct-2512-q4_K_M"
DEFAULT_VISION_MODEL = "openai:ministral-3:8b-instruct-2512-q4_K_M"


def create_agent(harness: Harness, model: str | None = None) -> Agent:
    """Create a Pydantic AI agent with tools bound to a harness instance.

    Args:
        harness: The harness instance to bind tools to.
        model: Model string (e.g. "ollama:mixtral", "ollama:llava",
               "openai:gpt-4o"). Defaults to ollama:mixtral.
    """
    agent = Agent(model or DEFAULT_MODEL, system_prompt=SYSTEM_PROMPT)

    @agent.tool
    def get_project_state(ctx: RunContext[None]) -> str:
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

    @agent.tool
    def get_event_history(ctx: RunContext[None], limit: int = 10) -> str:
        """Get recent project events with timestamps and provenance."""
        events = harness._ledger.events(harness.project_id)
        if not events:
            return "No events recorded."
        lines = []
        for e in events[-limit:]:
            prov = f" by {e.provenance.actor}" if e.provenance else ""
            lines.append(f"[{e.occurred_at}] {e.payload.next_action}{prov}")
        return "\n".join(lines)

    @agent.tool
    def run_harness(ctx: RunContext[None], goal: str) -> str:
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

    @agent.tool
    def search_memory(ctx: RunContext[None], query: str = "", namespace: str = "") -> str:
        """Search structured memory. Filter by namespace (working, episodic, semantic, procedural) or query content."""
        ns = namespace or None
        memories = harness._memory.query(namespace=ns)
        if query:
            memories = [m for m in memories if query.lower() in m.content.lower()]
        if not memories:
            return "No matching memories."
        lines = [f"[{m.namespace}/{m.scope}] {m.content}" for m in memories]
        return "\n".join(lines)

    @agent.tool
    def add_memory(ctx: RunContext[None], content: str, namespace: str = "episodic", scope: str = "workspace:shallot") -> str:
        """Add a new memory entry. Use for facts, decisions, or observations worth remembering.

        HITL-gated (UX research 5.4): canonical memory writes require human approval before they
        become persistent fact. If pending, the entry is NOT stored and the caller must approve it.
        """
        from shallot_harness.memory import Memory

        if not harness.request_approval("memory.write", f"memory:{scope}", {"content": content, "namespace": namespace}):
            return "⏳ Minne väntar på godkännande (action pending). Använd approve_action för att godkänna innan det sparas."
        m = Memory.create(namespace=namespace, scope=scope, content=content)
        harness._memory.add(m)
        return f"Memory stored: {m.memory_id} ({m.namespace}/{m.scope})"

    @agent.tool
    def approve_action(ctx: RunContext[None], action_id: str) -> str:
        """Approve a pending HITL action by its ID."""
        from uuid import UUID

        try:
            ok = harness._policy.approve(UUID(action_id))
        except (ValueError, TypeError):
            return f"Invalid action_id: {action_id!r}. Use a pending ID from get_approvals."
        return "Approved." if ok else "Action not found or already processed."

    @agent.tool
    def get_budget_status(ctx: RunContext[None]) -> str:
        """Check remaining cloud budget for this month (€20 limit)."""
        remaining = harness._policy._budget.remaining()
        return f"Budget remaining: €{remaining:.2f} / €20.00"

    return agent
