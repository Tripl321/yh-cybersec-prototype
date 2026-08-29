import subprocess
from pathlib import Path

from shallot_harness.harness import Harness
from shallot_harness.stub_reasoner import StubReasoner


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True, check=True)


def test_harness_full_lifecycle(tmp_path):
    _init_repo(tmp_path)
    reasoner = StubReasoner(next_action="build policy gate", action_kind="issue.create")

    harness = Harness(
        project_id="shallot",
        repo_path=str(tmp_path),
        db_path=str(tmp_path.parent / "harness_test.db"),
        reasoner=reasoner,
    )

    result = harness.run(goal="Continue SHALLOT prototype")

    assert result["state"].project_id == "shallot"
    assert result["state"].next_action == "build policy gate"
    assert result["verdict"].allowed
    assert reasoner.call_count == 1
    assert reasoner.last_request.git_branch == "main"
    assert not reasoner.last_request.dirty

    harness.close()


def test_harness_persists_state_across_runs(tmp_path):
    _init_repo(tmp_path)
    r1 = StubReasoner(next_action="step 1")
    r2 = StubReasoner(next_action="step 2")

    h1 = Harness("shallot", str(tmp_path), str(tmp_path / "db"), r1)
    h1.run()
    h1.close()

    h2 = Harness("shallot", str(tmp_path), str(tmp_path / "db"), r2)
    state = h2.current_state()
    assert state is not None
    assert state.next_action == "step 1"

    h2.run()
    state2 = h2.current_state()
    assert state2.next_action == "step 2"
    h2.close()


def test_harness_passes_memory_context(tmp_path):
    _init_repo(tmp_path)
    reasoner = StubReasoner()
    harness = Harness("shallot", str(tmp_path), str(tmp_path / "db"), reasoner)

    from shallot_harness.memory import Memory

    harness._memory.add(Memory.create("semantic", "workspace:shallot", "important fact"))
    harness.run()
    assert "important fact" in reasoner.last_request.memory_context
    harness.close()


def test_harness_rejects_budget_exceeded(tmp_path):
    _init_repo(tmp_path)
    from shallot_harness.policy import BudgetTracker

    reasoner = StubReasoner(action_kind="cloud.infer")
    budget = BudgetTracker(monthly_limit_eur=0.0)
    harness = Harness(
        "shallot", str(tmp_path), str(tmp_path / "db"), reasoner,
        policy=__import__("shallot_harness.policy", fromlist=["PolicyGate"]).PolicyGate(budget=budget),
    )

    result = harness.run()
    assert not result["verdict"].allowed
    assert result["verdict"].reason == "budget_exceeded"
    harness.close()


def test_harness_records_event_in_ledger(tmp_path):
    _init_repo(tmp_path)
    reasoner = StubReasoner()
    harness = Harness("shallot", str(tmp_path), str(tmp_path / "db"), reasoner)
    harness.run()

    events = harness._ledger.events("shallot")
    assert len(events) == 1
    assert events[0].provenance is not None
    assert events[0].provenance.actor == "shallot-harness"
    harness.close()
