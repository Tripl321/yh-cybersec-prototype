"""Tests for Agno agent tools."""

import subprocess
from pathlib import Path

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
        agent = create_agent(h, model="ollama:qwen3:14b")
        assert agent is not None
        # Agno stores tools as list of Function objects with .name
        all_tool_names = set()
        for t in agent.tools or []:
            name = getattr(t, "name", None) or getattr(t, "__name__", None)
            if name:
                all_tool_names.add(name)
            # Toolkit objects have .functions
            if hasattr(t, "functions"):
                for fn in t.functions.values():
                    all_tool_names.add(getattr(fn, "name", str(fn)))
        # Fallback: also check via tool.name attribute on Function wrappers
        if not all_tool_names and hasattr(agent, "tools"):
            for t in agent.tools:
                if hasattr(t, "name"):
                    all_tool_names.add(t.name)
        expected = {
            "get_project_state",
            "get_event_history",
            "run_harness",
            "search_memory",
            "add_memory",
            "approve_action",
            "get_budget_status",
        }
        assert expected.issubset(all_tool_names), f"Missing: {expected - all_tool_names} got {all_tool_names}"
        h.close()

    def test_agent_accepts_model_override(self, tmp_path):
        h = _make_harness(tmp_path)
        agent = create_agent(h, model="ollama:qwen3:14b")
        assert agent.model is not None
        h.close()
