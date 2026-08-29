"""Reasoner protocol — what the LLM backend must implement."""

from typing import Protocol

from pydantic import BaseModel


class ReasonerRequest(BaseModel):
    """Input to the reasoner: context, memory, current state."""

    project_id: str
    current_issue: int | None
    git_branch: str
    git_head: str
    dirty: bool
    recent_commits: list[str]
    open_issues: list[str]
    memory_context: list[str]
    goal: str


class ReasonerResponse(BaseModel):
    """Structured output from the reasoner."""

    next_action: str
    action_kind: str
    target: str
    reasoning: str
    confidence: float


class Reasoner(Protocol):
    """Contract for LLM backends. Ollama, GreenPT, Mistral all implement this."""

    def reason(self, request: ReasonerRequest) -> ReasonerResponse: ...
