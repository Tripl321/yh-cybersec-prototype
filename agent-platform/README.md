# AgentOS — SHALLOT Harness Platform

A self-building agent platform built on [Agno AgentOS 3.0](https://docs.agno.com).
This is the **SHALLOT Harness**: the personal agent platform for project
management, development, research, cybersecurity, and physical builds. It
starts with SHALLOT as its single workspace but can later hold separate
personal and project memories.

## What ships

Three platform agents, one team, and two reference workflows, all running in a
single FastAPI app backed by PostgreSQL + pgvector:

- **platform-builder** — creates agents, teams, and workflows through the
  safe Studio registry (create/edit/publish run; archive/delete pause for human
  approval).
- **platform-manager** — read-only observer of the runtime: usage, token spend,
  runs, tools, evals, schedules, and the deployment check.
- **platform-engineer** — read-only codebase guide: explains how the platform
  is wired from source, grounded in real file paths.
- **agno** (team) — the platform lead. Delegates builds to Builder, health to
  Manager, and source questions to Engineer, and files decisions to the shared
  notebook, entities, and notes.
- **deployment-check** (workflow) — 10 no-model-call readiness checks (DB,
  runtime, OpenAI key, AgentOS URL, MCP, Slack, components, registry, schedules,
  poller). Runs on demand or daily.
- **run-evals** (workflow) — runs the eval suite tagged by `EVALS_TAG`
  (default `smoke`). Ships disabled because it spends model calls.

Shared, registered capabilities used by Studio-built components:
`shared-notes` notebook (file system), `shared-knowledge` (pgvector RAG),
`shared-learning` (per-user memory), result offloading, and the workflow
functions (`extract_json`, `extract_urls`, `json_to_csv`, `csv_to_markdown_table`,
`content_to_file`).

## Architecture

```text
FastAPI (app/main.py)
  └── AgentOS
        ├── agents:   platform-builder, platform-manager, platform-engineer
        ├── team:     agno
        ├── workflows: deployment-check, run-evals
        ├── registry: shared tools or Studio-built components
        ├── scheduler: daily deployment-check + run-evals (opt-in)
        ├── MCP server: /mcp (streamable HTTP, apply-anywhere)
        └── db:    Postgres + pgvector (sessions, memory, knowledge, evals, schedules)
```

- **DB**: PostgreSQL + pgvector (`compose.yaml` runs `agnohq/pgvector:18`).
- **Model**: local-first — Ollama `ministral-3:8b` on the Fedora control node
  (`OLLAMA_HOST`, default `http://fedora:11434`). Set `MODEL_PROVIDER=openai`
  in `.env` to opt back into OpenAI `gpt-5.6` (judge evals / heavier runs).
  See `app/settings.py`.
- **Security**: `RUNTIME_ENV=dev` disables JWT (`authorization=False` is derived
  from it); production requires `JWT_VERIFICATION_KEY`/`JWT_JWKS_FILE`. MCP
  OAuth is on only when `MCP_CONNECT_SECRET` is set.

## Quick start (Docker)

```bash
cp example.env .env
# put a real OPENAI_API_KEY in .env
docker compose up --build
```

- API/UI: http://localhost:8000  (AgentOS serves AgentUI at `/`)
- MCP: http://localhost:8000/mcp
- Docs: https://docs.agno.com

Run the deployment check on demand:

```bash
curl -X POST http://localhost:8000/workflows/deployment-check/runs
```

Verify the MCP surface end to end:

```bash
./scripts/mcp_check.sh
```

## Local development (no Docker)

```bash
./scripts/venv_setup.sh          # creates .venv + installs -e .[dev]
source .venv/bin/activate
python -m app.main               # serves AgentOS on :8000 with reload
```

Requires a Postgres/pgvector instance reachable via the `DB_*` env vars
(defaults: `localhost:5432/ai`, user/pass `ai/ai`).

Lint and typecheck before committing:

```bash
./scripts/format.sh
./scripts/validate.sh
```

## Troubleshooting

- **Ollama runs on CPU after Fedora boots.** If `ollama ps` shows `PROCESSOR
  100% CPU` (RTX 4080 idle), the service booted before the GPU driver was
  ready: `systemctl restart ollama` on the Fedora node and confirm
  `ollama ps` shows `100% GPU`.

## Schedules

Registered on boot by `app/schedules.py` (idempotent, fail-soft):

| Schedule | Cron (UTC) | Enabled by default |
|---|---|---|
| deployment-check | `0 13 * * *` | yes (`ENABLE_DEPLOY_CHECK` re-asserts it) |
| run-evals | `0 14 * * *` | no (uses model calls — toggle from the UI) |

## Evals

The eval suite lives in `evals/` and validates platform behavior (builder
safety, manager health reading, engineer source grounding, agno memory and
honest dispatch) with `AgentAsJudgeEval` and `ReliabilityEval`. Results are
persisted via `eval_db` and visible in the AgentOS UI.

```bash
python -m evals --tag smoke       # fast, free-ish (no judge on smoke runners)
python -m evals                   # full suite, LLM-judged
```

Setup/teardown hooks in `evals/hooks.py` snapshot and hard-delete anything a
case creates (components, schedules, learning rows, notes), refusing rather
than guessing when a snapshot looks incomplete.

## Structure

```text
agents/       # platform agents (builder, manager, engineer)
app/          # shared runtime: main.py, registry, schedules, notes, knowledge,
              # learning, offload, functions, settings, config.yaml
db/           # Postgres connection helpers (url, session)
evals/        # eval suite (cases, hooks, runner)
scripts/      # entrypoint + dev tooling
teams/        # agno team lead
workflows/    # deployment-check, run-evals
Dockerfile
compose.yaml
requirements.txt   # pinned lockfile for the container image
pyproject.toml     # project metadata + dev tooling config
```
