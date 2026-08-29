"""Tests for MCP server interface."""

import subprocess
from pathlib import Path

from shallot_harness.harness import Harness
from shallot_harness import mcp_server as _mcp_mod
from shallot_harness.mcp_server import get_project_state, run_harness, get_events
from shallot_harness.stub_reasoner import StubReasoner


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True, check=True)


def test_mcp_get_state_empty(tmp_path):
    _init_repo(tmp_path)
    harness = Harness("shallot", str(tmp_path), str(tmp_path.parent / "mcp_test.db"), StubReasoner())
    _mcp_mod._harness = harness
    result = get_project_state()
    assert "No state recorded" in result
    harness.close()
    _mcp_mod._harness = None


def test_mcp_run_produces_state(tmp_path):
    _init_repo(tmp_path)
    harness = Harness("shallot", str(tmp_path), str(tmp_path.parent / "mcp_test.db"), StubReasoner())
    _mcp_mod._harness = harness
    result = run_harness()
    assert "Next action:" in result
    assert "continue prototype" in result
    harness.close()
    _mcp_mod._harness = None


def test_mcp_get_events(tmp_path):
    _init_repo(tmp_path)
    harness = Harness("shallot", str(tmp_path), str(tmp_path.parent / "mcp_test.db"), StubReasoner())
    _mcp_mod._harness = harness
    run_harness()
    result = get_events()
    assert "continue prototype" in result
    harness.close()
    _mcp_mod._harness = None
