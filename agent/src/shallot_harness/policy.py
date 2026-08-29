"""Policy gate — idempotent action approval, budget limits, HITL."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict


class ApprovalRequired(Exception):
    """Raised by a deferred tool when an action needs human approval before it can run.

    Carries the pending action_id so the caller (CLI, UI) can surface an approval card
    and later resolve it via PolicyGate.approve / the approve_action tool.
    """

    def __init__(self, action_id: UUID) -> None:
        self.action_id = action_id
        super().__init__(f"Action {action_id} requires human approval")


class Action(BaseModel):
    """What the agent wants to do."""

    model_config = ConfigDict(frozen=True)

    action_id: UUID
    kind: Literal[
        "code.write",
        "code.delete",
        "issue.create",
        "issue.update",
        "pr.create",
        "memory.promote",
        "memory.write",
        "memory.forget",
        "cloud.infer",
    ]
    target: str
    payload: dict
    requested_at: datetime

    @classmethod
    def create(cls, kind: str, target: str, payload: dict | None = None) -> "Action":
        return cls(
            action_id=uuid4(),
            kind=kind,
            target=target,
            payload=payload or {},
            requested_at=datetime.now(UTC),
        )


class PolicyVerdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: UUID
    allowed: bool
    reason: str
    requires_approval: bool
    budget_remaining_eur: float | None = None


class BudgetTracker:
    """Simple monthly cloud spend tracker. €20 limit per ADR 0010."""

    def __init__(self, monthly_limit_eur: float = 20.0) -> None:
        self._limit = monthly_limit_eur
        self._spent: dict[str, float] = {}  # YYYY-MM → total

    def record(self, month: str, cost_eur: float) -> None:
        self._spent[month] = self._spent.get(month, 0.0) + cost_eur

    def remaining(self, month: str | None = None) -> float:
        if month is None:
            month = datetime.now(UTC).strftime("%Y-%m")
        return max(0.0, self._limit - self._spent.get(month, 0.0))

    def can_spend(self, cost_eur: float, month: str | None = None) -> bool:
        return self.remaining(month) >= cost_eur


class ApprovalStore:
    """In-memory HITL approval tracker. Persists later via Store seam."""

    def __init__(self) -> None:
        self._pending: dict[UUID, Action] = {}
        self._approved: set[UUID] = set()

    def submit(self, action: Action) -> None:
        self._pending[action.action_id] = action

    def approve(self, action_id: UUID) -> bool:
        if action_id in self._pending:
            self._approved.add(action_id)
            return True
        return False

    def is_approved(self, action_id: UUID) -> bool:
        return action_id in self._approved

    def pending(self) -> list[Action]:
        return list(self._pending.values())


class PolicyGate:
    """Central gatekeeper. Idempotent: same action_id → same verdict."""

    def __init__(
        self,
        budget: BudgetTracker | None = None,
        approvals: ApprovalStore | None = None,
    ) -> None:
        self._budget = budget or BudgetTracker()
        self._approvals = approvals or ApprovalStore()
        self._verdicts: dict[UUID, PolicyVerdict] = {}

    # Rules: which action kinds need approval, which route to cloud
    _APPROVAL_REQUIRED: set[str] = {"code.write", "code.delete", "pr.create", "memory.promote", "memory.write", "memory.forget"}
    _CLOUD_KINDS: set[str] = {"cloud.infer"}
    _CLOUD_COST_EUR: float = 0.01  # placeholder per-inference cost

    def check(self, action: Action) -> PolicyVerdict:
        """Idempotent: returns cached verdict if already decided."""
        if action.action_id in self._verdicts:
            return self._verdicts[action.action_id]

        requires_approval = action.kind in self._APPROVAL_REQUIRED
        budget_remaining = self._budget.remaining()

        if action.kind in self._CLOUD_KINDS:
            if not self._budget.can_spend(self._CLOUD_COST_EUR):
                verdict = PolicyVerdict(
                    action_id=action.action_id,
                    allowed=False,
                    reason="budget_exceeded",
                    requires_approval=False,
                    budget_remaining_eur=budget_remaining,
                )
                self._verdicts[action.action_id] = verdict
                return verdict

        if requires_approval:
            self._approvals.submit(action)
            verdict = PolicyVerdict(
                action_id=action.action_id,
                allowed=False,
                reason="awaiting_approval",
                requires_approval=True,
                budget_remaining_eur=budget_remaining,
            )
        else:
            verdict = PolicyVerdict(
                action_id=action.action_id,
                allowed=True,
                reason="auto_approved",
                requires_approval=False,
                budget_remaining_eur=budget_remaining,
            )

        self._verdicts[action.action_id] = verdict
        return verdict

    def approve(self, action_id: UUID) -> bool:
        """Human approves a pending action. Returns False if not found."""
        if self._approvals.approve(action_id):
            verdict = self._verdicts.get(action_id)
            if verdict:
                self._verdicts[action_id] = PolicyVerdict(
                    action_id=action_id,
                    allowed=True,
                    reason="human_approved",
                    requires_approval=True,
                    budget_remaining_eur=verdict.budget_remaining_eur,
                )
                return True
        return False

    def is_allowed(self, action: Action) -> bool:
        verdict = self.check(action)
        if verdict.allowed:
            return True
        if verdict.requires_approval:
            return self._approvals.is_approved(action.action_id)
        return False
