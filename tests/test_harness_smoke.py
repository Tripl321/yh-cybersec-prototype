"""Smoke test for the SHALLOT Harness agent (D9 build seam).

Run on the RTX 4080 Fedora box: `pytest -q tests/test_harness_smoke.py`.
Cannot run in the charting env (no agno / ollama / GPU).
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def _load():
    spec = importlib.util.spec_from_file_location("agno_agent", REPO / "agno_agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def agent_mod():
    return _load()


def test_agent_builds(agent_mod):
    assert agent_mod.shallot is not None
    assert agent_mod.shallot.name == "SHALLOT"


def test_run_allowlist_allows_tests(agent_mod):
    assert agent_mod._validate_run_command("pytest -q") == ""
    assert agent_mod._validate_run_command("ruff check .") == ""
    assert agent_mod._validate_run_command("npm run build") == ""


def test_run_allowlist_denies_egress(agent_mod):
    assert "denied" in agent_mod._validate_run_command("curl https://evil.com")
    assert "denied" in agent_mod._validate_run_command("sudo ls")
    assert "not in allowlist" in agent_mod._validate_run_command("git push origin main")
    assert "path escapes" in agent_mod._validate_run_command("cat /etc/passwd")


def test_run_allowlist_denies_shell_injection(agent_mod):
    assert "shell metacharacters" in agent_mod._validate_run_command("pytest && curl x")


def test_get_db_default_is_sqlite(agent_mod, monkeypatch):
    monkeypatch.delenv("SHALLOT_DB_URL", raising=False)
    db = agent_mod.get_db()
    assert type(db).__name__ == "SqliteDb"
