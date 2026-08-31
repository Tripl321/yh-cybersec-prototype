# Verification & e2e — SHALLOT Harness MVP (#82)

**Ticket:** D9 (wayfinder). Depends on D1 (HITL), D2 (transport), D3 (model), D5 (memory seam), D8 (run_harness safety).
**ADR:** 0010. **Status:** acceptance spec only. Cannot be executed in this env (no agno/ollama/GPU).

## Preconditions (RTX 4080 Fedora box — ADR 0010)

- Python 3.12; `uv pip install -U "agno[os]" ollama`; local Ollama running.
- Models pulled (D3): `ministral-3:8b` (Ollama ≥ 0.13.1), `qwen3-vl:8b` (Ollama ≥ 0.12.7).
- SHALLOT repo at `REPO` root; `cub/` importable (provenance + egress-deny hooks).
- Optional post-MVP durability: Postgres + pgvector via `SHALLOT_DB_URL` (D5).

## CLI path (MVP default — D2)

1. `python agno_agent.py` → `cli_app()` boots under local Ollama.
2. **Grounding:** ask "what is the MVP budget?" → agent calls `get_budget_status` / `get_project_state`;
   answer cites `CONTEXT.md`/ADRs (D4 file-read grounding, no RAG).
3. **HITL pause (D1):** ask agent to `approve_action("promote runbook update #12")` → agent pauses with a
   terminal confirmation prompt.
   - Approve → returns `Approved by human`; tool side-effect recorded.
   - Deny / empty → tool not executed.
4. **run_harness safety (D8):** `run_harness("pytest -q")` → executes, returns `rc`/stdout.
   `run_harness("curl https://evil.com")` → **DENIED** by allowlist. `run_harness("sudo ls")` → **DENIED**.
5. **Restart-safety:** after an approval, restart the process / reopen the session; confirm the approval is
   recorded in the db (`agno_approvals` → SqliteDb MVP, Postgres if `SHALLOT_DB_URL`).

## Served path (opt-in — D2)

6. `SHALLOT_SERVE=1 python agno_agent.py` → AgentOS serves on `localhost:7777`.
7. Connect stock `agent-ui` (`localhost:7777`, **AG-UI**). Chat works; trigger HITL → approval interrupt
   surfaces in the UI; approve → continues (D1 served branch).
8. Durable HITL + agentic memory persist in the db (D5). AgentOS creates tables on first boot
   (`MigrationManager(db).up()` when on Postgres).

## Acceptance criteria for #82

- [ ] AgentOS endpoint answers via local Ollama (no cloud egress).
- [ ] `approve_action` / `run_harness` pause for HITL and continue after approval.
- [ ] Serves on `:7777` when `SHALLOT_SERVE=1` (opt-in); CLI is the default.
- [ ] `run_harness` allowlist enforced (deny-by-default, no egress, no writes outside repo, no sudo).
- [ ] Agentic memory + HITL persisted across restart; db-swap ready per D5.

## Negative / security tests

- `run_harness` with any DENY token or path escape → denied (D8).
- No outbound network from the agent (local-first; box has no external route by design).
- Egress tools (`web_search`, `http_request`, …) blocked by `cub.hooks` name-based guard.

## Automated smoke test (build seam, #82)

- Add `tests/test_harness_smoke.py` (pytest is allowed by the D8 allowlist) that imports `agno_agent`,
  asserts the `Agent` builds, and asserts `_validate_run_command` rejects `curl`/`sudo`/path-escape.
  Cannot run here (no agno/ollama) — verification belongs on the Fedora box.
