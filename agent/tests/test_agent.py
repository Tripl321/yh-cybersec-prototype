"""Tests for Pydantic AI agent tools."""

import subprocess
from pathlib import Path

from pydantic_ai.models.test import TestModel

from shallot_harness.agent import create_agent
from shallot_harness.harness import Harness
from shallot_harness.stub_reasoner import StubReasoner


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True, check=True)


def _make_harness(tmp_path: Path) -> Harness:
    return Harness(
        "shallot",
        str(tmp_path),
        str(tmp_path / "agent_test.db"),
        StubReasoner(),
    )


class TestAgentTools:
    def test_agent_creates_with_all_tools(self, tmp_path):
        h = _make_harness(tmp_path)
        agent = create_agent(h, model=TestModel())
        assert agent is not None
        all_tool_names = set()
        for ts in agent.toolsets:
            all_tool_names.update(ts.tools.keys())
        expected = {
            "get_project_state",
            "get_event_history",
            "run_harness",
            "search_memory",
            "add_memory",
            "approve_action",
            "get_budget_status",
        }
        assert expected.issubset(all_tool_names), f"Missing: {expected - all_tool_names}"
        h.close()

    def test_agent_accepts_model_override(self, tmp_path):
        h = _make_harness(tmp_path)
        agent = create_agent(h, model=TestModel())
        assert agent._model is not None
        h.close()
