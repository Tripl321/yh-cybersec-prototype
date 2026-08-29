"""Tests for FastAPI web interface."""

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from shallot_harness.api import app, init_harness
from shallot_harness.harness import Harness
from shallot_harness.stub_reasoner import StubReasoner


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True, check=True)


from shallot_harness import api as _api_mod


@pytest.fixture()
def client(tmp_path):
    _init_repo(tmp_path)
    db_path = tmp_path / "test_api.db"
    harness = Harness(
        project_id="shallot",
        repo_path=str(tmp_path),
        db_path=str(db_path),
        reasoner=StubReasoner(next_action="build tests", action_kind="issue.create"),
    )
    init_harness(harness)
    with TestClient(app) as c:
        yield c
    harness.close()
    _api_mod._harness = None


def test_ui_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "SHALLOT Harness" in r.text


def test_state_initially_none(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    assert r.json()["state"] is None


def test_run_produces_state(client):
    r = client.post("/api/run")
    assert r.status_code == 200
    data = r.json()
    assert data["state"]["project_id"] == "shallot"
    assert data["state"]["next_action"] == "build tests"
    assert data["verdict"]["allowed"] is True


def test_events_after_run(client):
    client.post("/api/run")
    r = client.get("/api/events")
    assert r.status_code == 200
    assert len(r.json()["events"]) == 1


def test_memory_initially_empty(client):
    r = client.get("/api/memory")
    assert r.status_code == 200
    assert r.json()["memories"] == []


def test_run_multiple_times(client):
    client.post("/api/run")
    client.post("/api/run", json={"goal": "second run"})
    r = client.get("/api/events")
    assert len(r.json()["events"]) == 2

    state = client.get("/api/state").json()["state"]
    assert state["next_action"] == "build tests"
