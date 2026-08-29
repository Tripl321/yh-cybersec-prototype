"""SHALLOT Harness canonical models — immutable, provenance-tagged."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict


class Provenance(BaseModel):
    """Who/what initiated an action. Required for memory promotion and audit."""

    model_config = ConfigDict(frozen=True)

    actor: str
    method: Literal["cli", "api", "mcp", "acp", "system", "human"]
    initiated_at: datetime


class ProjectState(BaseModel):
    """Canonical snapshot of a project's status."""

    model_config = ConfigDict(frozen=True)

    project_id: str
    current_issue: int | None
    next_action: str
    verification_criterion: str
    observed_at: datetime


class ProjectEvent(BaseModel):
    """Append-only event. Source of truth; ProjectState is derived."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID
    kind: Literal["status.recorded"]
    project_id: str
    occurred_at: datetime
    payload: ProjectState
    provenance: Provenance | None = None

    @classmethod
    def status_recorded(
        cls, state: ProjectState, provenance: Provenance | None = None
    ) -> "ProjectEvent":
        return cls(
            event_id=uuid4(),
            kind="status.recorded",
            project_id=state.project_id,
            occurred_at=state.observed_at,
            payload=state,
            provenance=provenance,
        )
