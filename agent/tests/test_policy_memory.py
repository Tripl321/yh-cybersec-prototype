from datetime import UTC, datetime, timedelta

from shallot_harness.memory import Memory, MemoryStore
from shallot_harness.policy import (
    Action,
    ApprovalStore,
    BudgetTracker,
    PolicyGate,
)


def _make_action(kind: str = "issue.create") -> Action:
    return Action.create(kind=kind, target="test", payload={"test": True})


class TestPolicyGate:
    def test_auto_approved_actions(self):
        gate = PolicyGate()
        action = _make_action("issue.create")
        verdict = gate.check(action)
        assert verdict.allowed
        assert verdict.reason == "auto_approved"
        assert not verdict.requires_approval

    def test_approval_required_actions(self):
        gate = PolicyGate()
        action = _make_action("code.write")
        verdict = gate.check(action)
        assert not verdict.allowed
        assert verdict.requires_approval
        assert verdict.reason == "awaiting_approval"

    def test_human_approval_flows_through(self):
        gate = PolicyGate()
        action = _make_action("code.write")
        gate.check(action)
        assert not gate.is_allowed(action)

        gate.approve(action.action_id)
        assert gate.is_allowed(action)

    def test_budget_rejects_cloud_when_exceeded(self):
        budget = BudgetTracker(monthly_limit_eur=0.0)
        gate = PolicyGate(budget=budget)
        action = _make_action("cloud.infer")
        verdict = gate.check(action)
        assert not verdict.allowed
        assert verdict.reason == "budget_exceeded"

    def test_budget_allows_cloud_within_limit(self):
        budget = BudgetTracker(monthly_limit_eur=100.0)
        gate = PolicyGate(budget=budget)
        action = _make_action("cloud.infer")
        verdict = gate.check(action)
        assert verdict.allowed
        assert verdict.budget_remaining_eur == 100.0

    def test_verdicts_are_idempotent(self):
        gate = PolicyGate()
        action = _make_action("code.write")
        v1 = gate.check(action)
        v2 = gate.check(action)
        assert v1 is v2

    def test_budget_tracking(self):
        budget = BudgetTracker(monthly_limit_eur=20.0)
        assert budget.remaining("2026-08") == 20.0
        budget.record("2026-08", 5.0)
        assert budget.remaining("2026-08") == 15.0
        assert budget.can_spend(15.0, "2026-08")
        assert not budget.can_spend(16.0, "2026-08")


class TestMemoryStore:
    def test_add_and_get(self):
        store = MemoryStore()
        m = Memory.create("working", "session", "test content")
        store.add(m)
        assert store.get(m.memory_id) == m

    def test_query_by_namespace(self):
        store = MemoryStore()
        store.add(Memory.create("working", "session", "w1"))
        store.add(Memory.create("episodic", "session", "e1"))
        working = store.query(namespace="working")
        assert len(working) == 1
        assert working[0].content == "w1"

    def test_query_by_scope(self):
        store = MemoryStore()
        store.add(Memory.create("working", "person:johannes", "j"))
        store.add(Memory.create("working", "workspace:shallot", "s"))
        personal = store.query(scope="person:johannes")
        assert len(personal) == 1

    def test_ttl_expires(self):
        store = MemoryStore()
        m = Memory.create("working", "session", "ephemeral", ttl_hours=-1)
        store.add(m)
        assert store.get(m.memory_id) is None
        assert len(store.query()) == 0

    def test_promote(self):
        store = MemoryStore()
        m = Memory.create("semantic", "person:johannes", "facts")
        store.add(m)
        assert store.promote(m.memory_id, proof="eval_pass_2026-08-26")
        promoted = store.get(m.memory_id)
        assert promoted.promoted
        assert promoted.promotion_proof == "eval_pass_2026-08-26"

    def test_forget(self):
        store = MemoryStore()
        m = Memory.create("working", "session", "sensitive")
        store.add(m)
        assert store.forget(m.memory_id)
        assert store.get(m.memory_id) is None
        assert not store.forget(m.memory_id)

    def test_include_expired(self):
        store = MemoryStore()
        m = Memory.create("working", "session", "expired", ttl_hours=-1)
        store.add(m)
        assert len(store.query()) == 0
        assert len(store.query(include_expired=True)) == 1
