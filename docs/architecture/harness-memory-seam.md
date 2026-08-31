# Memory backend migration seam — SHALLOT Harness (MVP → post-MVP)

**Ticket:** D5 (wayfinder). Depends on D4 (RAG deferred) and D2 (transport).
**ADR:** 0010 (Postgres+pgvector post-MVP, durable/restart-safe HITL).
**Status:** Spec only. No code changed yet (build seam for #82). Git is denied in this env.

## Current state (MVP)

- `agno_agent.py` constructs the agent with `db=SqliteDb(db_file="tmp/agents.db")`.
- `enable_agentic_memory=True` → user memories persist in the agent db (`agno_memories` table).
- HITL approvals (`requires_confirmation=True`) persist in the agent db (`agno_approvals` table) —
  this is the "durable / restart-safe HITL" ADR 0010 refers to.
- No `Knowledge`/RAG is wired (deferred by D4).
- The MVP transport is CLI-first (`cli_app()`); AgentOS.serve is opt-in (D2).

## Target (post-MVP, ADR 0010)

- **Relational state + agentic memory + approvals:** `PostgresDb(db_url=...)`.
- **Knowledge / vector search:** `PgVector` (hybrid) as the `Knowledge.vector_db` — only when RAG
  is added per D4.
- **Durable scheduling (Temporal):** workflows persist in the same `db`.

Agno's `db` parameter is a single interface implemented by `SqliteDb`, `PostgresDb`, `MongoDb`,
etc. (confirmed: `docs.agno.com/features/storage`, `docs.agno.com/memory/working-with-memories/postgres-memory`).
Swapping the backend is a constructor change, not a behavior change.

## The seam (non-breaking)

1. **`get_db()` factory** (module-level in `agno_agent.py`):
   - if `SHALLOT_DB_URL` is set → `PostgresDb(db_url=os.getenv("SHALLOT_DB_URL"))`
   - else → `SqliteDb(db_file="tmp/agents.db")` (MVP default)
   - pass its result to `Agent(db=...)` **and** to `AgentOS(db=...)` (the D2 serve path).
2. **Agentic memory + HITL need NO other code change** — they ride on the `db` swap. Agno creates
   `agno_memories` / `agno_approvals` / `agno_sessions` tables; on Postgres, run the idempotent
   `MigrationManager(db).up()` once on first boot.
3. **Knowledge/RAG (deferred):** when added (D4), build
   `Knowledge(vector_db=PgVector(table_name=..., db_url=SHALLOT_DB_URL, search_type=SearchType.hybrid, embedder=...))`
   behind the `harness/knowledge.py` loader from D4. The `db` swap already supplies the Postgres
   service; the `pgvector` extension is added via the pgvector container.
4. **Tool contracts and system prompt are unchanged.** Only the db *construction* point changes;
   everything the agent exposes (tools, HITL behavior, grounding) is identical.

## What must NOT be hardcoded

- `SqliteDb(db_file=...)` literal → replace with `get_db()`.
- Any direct file path for memory state → goes through `db`.

## Verification (post-MVP, on the RTX 4080 Fedora box)

- Set `SHALLOT_DB_URL=postgresql+psycopg://ai:ai@localhost:5532/ai`, run `MigrationManager(db).up()`,
  boot AgentOS, and confirm sessions / memories / approvals survive a restart and are visible across
  replicas. Then add the `Knowledge`/`PgVector` layer behind `harness/knowledge.py` and confirm
  hybrid search returns SHALLOT docs.
