from datetime import UTC, datetime

import pytest

from shallot_harness.ledger import ProjectLedger
from shallot_harness.models import ProjectEvent, ProjectState, Provenance


def _make_state(**overrides) -> ProjectState:
    defaults = dict(
        project_id="shallot",
        current_issue=73,
        next_action="Create owned state schemas",
        verification_criterion="State is identical after restart",
        observed_at=datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
    )
    defaults.update(overrides)
    return ProjectState(**defaults)


def test_project_state_survives_restart(tmp_path):
    path = str(tmp_path / "harness.db")
    expected = _make_state()

    ledger = ProjectLedger(path)
    ledger.append(ProjectEvent.status_recorded(expected))
    ledger.close()

    restarted = ProjectLedger(path)
    assert restarted.state("shallot") == expected
    restarted.close()


def test_provenance_survives_restart(tmp_path):
    path = str(tmp_path / "harness.db")
    prov = Provenance(
        actor="johannes",
        method="cli",
        initiated_at=datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
    )
    state = _make_state()
    event = ProjectEvent.status_recorded(state, provenance=prov)

    ledger = ProjectLedger(path)
    ledger.append(event)
    ledger.close()

    restarted = ProjectLedger(path)
    events = restarted.events("shallot")
    assert len(events) == 1
    assert events[0].provenance == prov
    restarted.close()


def test_events_returns_chronological_order(tmp_path):
    path = str(tmp_path / "harness.db")
    ledger = ProjectLedger(path)

    states = [
        _make_state(next_action=f"step {i}", observed_at=datetime(2026, 8, 26, i, 0, tzinfo=UTC))
        for i in range(5)
    ]
    for s in states:
        ledger.append(ProjectEvent.status_recorded(s))

    events = ledger.events("shallot")
    assert len(events) == 5
    for i, e in enumerate(events):
        assert e.payload.next_action == f"step {i}"
    ledger.close()


def test_multiple_projects_isolated(tmp_path):
    path = str(tmp_path / "harness.db")
    ledger = ProjectLedger(path)

    ledger.append(ProjectEvent.status_recorded(_make_state(project_id="shallot")))
    ledger.append(ProjectEvent.status_recorded(_make_state(project_id="cub")))

    assert ledger.state("shallot") is not None
    assert ledger.state("cub") is not None
    assert ledger.events("shallot") != ledger.events("cub")
    ledger.close()


def test_state_returns_latest_event_payload(tmp_path):
    path = str(tmp_path / "harness.db")
    ledger = ProjectLedger(path)

    ledger.append(ProjectEvent.status_recorded(_make_state(next_action="first")))
    ledger.append(ProjectEvent.status_recorded(_make_state(next_action="second")))

    assert ledger.state("shallot").next_action == "second"
    ledger.close()


def test_empty_project_returns_none(tmp_path):
    path = str(tmp_path / "harness.db")
    ledger = ProjectLedger(path)
    assert ledger.state("nonexistent") is None
    assert ledger.events("nonexistent") == []
    ledger.close()
