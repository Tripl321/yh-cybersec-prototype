"""Stub reasoner for testing — returns deterministic responses."""

from shallot_harness.reasoner import ReasonerRequest, ReasonerResponse


class StubReasoner:
    """Deterministic reasoner for contract tests. No LLM calls."""

    def __init__(self, next_action: str = "continue prototype", action_kind: str = "issue.create") -> None:
        self._next_action = next_action
        self._action_kind = action_kind
        self._calls: list[ReasonerRequest] = []

    def reason(self, request: ReasonerRequest) -> ReasonerResponse:
        self._calls.append(request)
        return ReasonerResponse(
            next_action=self._next_action,
            action_kind=self._action_kind,
            target="test-target",
            reasoning="stub reasoning for testing",
            confidence=1.0,
        )

    @property
    def call_count(self) -> int:
        return len(self._calls)

    @property
    def last_request(self) -> ReasonerRequest | None:
        return self._calls[-1] if self._calls else None
