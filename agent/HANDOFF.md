# SHALLOT Harness Agent — Handoff

## Objective
Build a standalone SHALLOT Harness agent (Python, Pydantic AI) for the yh-cybersec-prototype project — a personal agent platform for project management, development, research, and cybersecurity work.
- Must support vision capabilities (photo analysis of breadboards/components for guided electronics help)

## Architecture (ADR 0010)
- Python 3.12+, Pydantic AI, PostgreSQL+pgvector, Temporal, Fedora control node, local Ollama, €20/mo cloud budget
- Issue #73 tracks delivery slices; labeled `ready-for-agent`
- Reuse existing OSS: Next.js dashboard (shadcn/ui) already in `shallot-setup/`
- Pydantic AI's `agent.to_web()` provides built-in chat UI with streaming, tool visualization, HITL — chosen over Vercel AI SDK
- Vision: snap photo of breadboard → agent guides/validates (requires vision-capable model like llava on Ollama)
- Project path: `/Users/johannes/Projects/Thesis Project/yh-cybersec-prototype/yh-cybersec-prototype`
- `uv` is the package manager for the Python agent

## Completed (45/45 tests passing)

### Core modules
- **Models** (`agent/src/shallot_harness/models.py`): `ProjectState`, `ProjectEvent`, `Provenance` — immutable Pydantic models
- **Store** (`agent/src/shallot_harness/store.py`): `Store` protocol + `SQLiteStore` (PostgreSQL swap-ready)
- **Ledger** (`agent/src/shallot_harness/ledger.py`): `ProjectLedger` — event replay → state reconstruction
- **Context** (`agent/src/shallot_harness/context/`): `GitContext`, `GitHubContext` (gh CLI), `RepoContext`
- **Policy** (`agent/src/shallot_harness/policy.py`): `PolicyGate`, `BudgetTracker` (€20/mo), `ApprovalStore` (HITL)
- **Memory** (`agent/src/shallot_harness/memory.py`): `MemoryStore` — TTL, forget/retraction, promotion with proof
- **Reasoner** (`agent/src/shallot_harness/reasoner.py`): `Reasoner` protocol + `StubReasoner`
- **Harness** (`agent/src/shallot_harness/harness.py`): orchestrator wiring context→reason→gate→record→remember

### Pydantic AI integration (fixed this session)
- **Agent** (`agent/src/shallot_harness/agent.py`): Pydantic AI Agent with 7 tools using `RunContext` (pydantic-ai 0.8 API)
- **CLI** (`agent/src/shallot_harness/cli.py`): `--model` flag for vision model override (e.g. `ollama:llava`)
- **otel stub** (`agent/src/shallot_harness/_otel_events_stub.py`): auto-installs `opentelemetry._events` shim via `sys.modules` (pydantic-ai 0.8 requires this but it's not in opentelemetry-api <=1.44.0)
- **`__init__.py`**: imports the otel stub early so it's always available
- **`tests/conftest.py`**: loads stub before test imports
- **API** (`agent/src/shallot_harness/api.py`): FastAPI REST endpoints
- **MCP Server** (`agent/src/shallot_harness/mcp_server.py`): MCP tools wrapping harness

### Dashboard
- Next.js dashboard stub pages created (`infrastructure.tsx`, `security.tsx`, `models.tsx`, `settings.tsx`) + `lib/utils.ts`

## Remaining
1. **Vision wiring** — user wants: snap photo of breadboard → agent analyzes components → guides user. Need to:
   - Confirm Ollama + llava (or llama3.2-vision) model is installed on the machine
   - Test `create_agent(harness, model="ollama:llava")` end-to-end with image input
   - Verify `agent.to_web()` supports image upload in its chat UI (check pydantic-ai docs for multimodal support)
2. **Agent tool tests** — expand `test_agent.py` to actually call tools and verify harness integration (currently only checks registration)
3. **Docker for PostgreSQL+pgvector** — not running locally; SQLite works for now
4. **Wire agent to real reasoner** — currently uses `StubReasoner`; swap for Ollama-backed or Temporal-backed reasoner per ADR 0010
5. **GitHub issue #73** — update with progress, mark completed slices

## Key Gotchas
- **pydantic-ai 0.8 API change**: tools with parameters MUST take `ctx: RunContext[DepType]` as first arg — bare parameters fail with "First parameter of tools that take context must be annotated with RunContext[...]"
- **otel stub**: must be imported before any `pydantic_ai` import; auto-installed via `sys.modules` patching in `__init__.py`
- **`agent.toolset`** is a method, not a property — use `agent.toolsets` (returns iterable of toolset objects with `.tools` dict)
