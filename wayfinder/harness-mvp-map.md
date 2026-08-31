# Wayfinder: SHALLOT Harness MVP (#82) — LOCAL DRAFT (not yet pushed)

This file is the human-readable chart of the wayfinder map for the SHALLOT Harness MVP.
It is the source for `push-wayfinder.sh`. Nothing here is published to GitHub until that
script is run in an environment with `gh` auth.

Legend: each ticket below becomes a GitHub child issue of the map, labelled `wayfinder:<type>`.

================================================================================
MAP ISSUE (label: wayfinder:map)
Title: Wayfinder: SHALLOT Harness MVP (#82)
================================================================================

## Destination
Complete the SHALLOT Harness MVP (ADR 0010 / #82): verified, AgentOS-served, HITL-working, local-first Agno agent.

## Notes
Stack: Agno v3 AgentOS, local Ollama (ministral-3:8b / qwen3-vl:8b), SqliteDb MVP → Postgres+pgvector post-MVP.
Skills to consult: grill-with-docs, grilling, domain-modeling, triage, code-review.
Local-first / zero-egress is non-negotiable (ADR 0006). Ground in NIST CSF 2.0 / 800-53r5 / MITRE ATT&CK / CIS v8.
Canonical tracker: GitHub issues (gh). GitHub Issues = canonical; Craft SHALLOT mirror is async.

## Decisions so far

- [HITL delivery mechanism (D1)](D1): MVP = local operator at the dev machine + Agno's built-in `requires_confirmation=True` terminal confirmation prompt under `cli_app()`. The served/PWA approval path (stock Agno `agent-ui`) only gets confirmation interrupts when AgentOS is served → deferred to D2. One HITL glossary term added to CONTEXT.md (covers Harness durable HITL + Cub deferred tools).
- [Transport: AgentOS serve vs cli (D2)](D2): MVP is CLI-first (`cli_app()`) default; AgentOS.serve(:7777) is opt-in behind `SHALLOT_SERVE=1`/`--serve` (one `shallot` Agent, two entrypoints). Served chat/approval adapter = AG-UI (Agno-native; ACP is Cub's stack, not used). `AgentOS.serve` is in-MVP but opt-in, keeping D7/D9 reachable without a server prerequisite.
- [Model reconciliation + vision policy (D3)](D3): `SHALLOT_MODEL=ministral-3:8b`; `VISION_MODEL=qwen3-vl:8b`. Harness↔Cub divergence intentional, no harmonize. Tags real/pullable; runtime verify on Fedora box. See `docs/research/harness-d3-model-policy.md`.
- [RAG / knowledge inclusion (D4)](D4): DEFER RAG to Postgres+pgvector (D5). MVP grounds via file-read tools; agentic memory ≠ doc RAG. Seam: `harness/knowledge.py` loader. See `docs/research/harness-d4-rag-scope.md`.
- [run_harness safety policy (D8)](D8): Allowlist = test/build/lint + read-only repo ops, deny-by-default. Enforced INSIDE run_harness (shlex.split, shell=False; cub.hooks egress-deny is name-based and does NOT cover shell content). No network egress, no writes outside repo, no sudo; containerized executor post-MVP. run_harness term + gap note added to CONTEXT.md.
- [Memory backend migration path (D5)](D5): Seam = `get_db()` factory (env SHALLOT_DB_URL → PostgresDb, else SqliteDb). Agentic memory + durable HITL ride on the db swap; Knowledge/PgVector added later behind harness/knowledge.py (D4). Spec: docs/architecture/harness-memory-seam.md. Minnes-backend term added to CONTEXT.md.
- [Verification & e2e (D9)](D9): Acceptance spec = docs/architecture/harness-verification.md. CLI default + opt-in :7777 serve; HITL pause→approve→continue; run_harness allowlist enforced; memory + HITL restart-safe. Build seam: tests/test_harness_smoke.py (cannot run here).
- [Observability in MVP (D6)](D6): NONE in MVP. Sessions/memories/HITL persist in db (D5) as minimal audit trail; post-MVP add local-only tracing (MLflow/Latitude).
- [Connect MCP git-server (D7)](D7): Implemented in agno_agent.py — opt-in `_git_tools()` via SHALLOT_GIT_MCP_URL (streamable-http) / SHALLOT_GIT_MCP_CMD (stdio); read-only by posture. Works CLI + served.
- [Agent gh/wayfinder access (D10)](D10): Provision fine-grained PAT (issues r/w, contents r) stored locally (.env.local / GH_TOKEN), never committed. Canonical tracker, not cloud inference; zero-egress for models holds.

## Not yet specified
- Durable scheduling / Temporal workers (post-MVP)
- Multi-worker scaling
- Cloud adapters (GreenPT / Mistral EU, €20/mo cap) — policy-gated, opt-in

## Out of scope
- Cub agent internals (ADR 0005–0007, separate)
- Full SHALLOT hardware/radio/demo-server work (own tickets)

================================================================================
TICKET D1 — HITL delivery mechanism  (label: wayfinder:grilling)  [RESOLVED — see Decisions so far]
================================================================================

## Question
How is `requires_confirmation=True` surfaced and resolved for the harness's two sensitive
tools (`approve_action`, `run_harness`)? Options: (a) interactive CLI prompt in `cli_app()`,
(b) PWA approval UI (ticket #81), (c) an AgentOS/AG-UI pause-and-ack channel. The build-ref
(#82) assumes an interactive approval surface; #81 owns the PWA approval UI. Decide the
MVP delivery mechanism and where the approval request/response lives.

## Context
- `agno_agent.py` sets `requires_confirmation=True` on `approve_action` and `run_harness`,
  but no delivery/transport for the pause is implemented yet.
- #81 (PWA) is the long-term approval surface; MVP may be simpler.
- Resolution must keep local-first / zero-egress (ADR 0006).

## Resolution shape
A decision: which mechanism for MVP, and a one-line seam so #81 can later replace it.

================================================================================
TICKET D2 — Transport: AgentOS serve vs cli  (label: wayfinder:grilling)  [RESOLVED — see Decisions so far]
================================================================================

## Question
build-ref (#82) step 4 specifies `AgentOS.serve("agentos:app")` on `localhost:7777`, but
`agno_agent.py` currently defaults its `__main__` to `cli_app()`. Decide the MVP transport
and the adapter shape (ACP / AG-UI / MCP per ADR 0010). Does MVP serve over AgentOS, or stay
CLI-first with serve added later?

## Context
- Tension captured as ticket D2 in planning handover.
- ADR 0010 names AgentOS as the runtime; adapter choice (ACP/AG-UI/MCP) is still open.
- D7 (MCP git-server) and D9 (verification) depend on this.

## Resolution shape
A decision on transport + adapter, recorded so D7/D9 can proceed.

================================================================================
TICKET D3 — Model reconciliation + vision policy  (label: wayfinder:research)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Confirm `ministral-3:8b` (ADR 0010) as the default harness model over `llama3.2` (ADR 0006),
and define the vision-model policy `VISION_MODEL=qwen3-vl:8b`. The two are different agents
(harness vs Cub) on different stacks — verify this is intentional and not a latent mismatch,
and confirm both models are available/runnable on the RTX 4080 Fedora box.

## Context
- `agno_agent.py` uses `ministral-3:8b`; `cub/*.py` used `llama3.2`. Intentional per ADR 0010
  (harness = Agno) vs ADR 0006 (Cub = Pydantic AI). Do NOT "harmonize".
- Must verify the Ollama model tags exist on the target hardware.

## Resolution shape
Research findings + a context pointer (branch `research/model-policy`) confirming the model
strings and availability. No code change required unless a tag is wrong.

================================================================================
TICKET D4 — RAG / knowledge inclusion in MVP  (label: wayfinder:research)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Should the harness include SHALLOT project docs as agent knowledge now, or defer knowledge
retrieval to the Postgres+pgvector backend (build-ref says post-MVP)? Weigh local-first
`enable_agentic_memory=True` (already on) against explicit RAG (see `cub/rag.py` experiment:
LanceDB + SentenceTransformerReranker + OllamaEmbedder dims=768). Decide MVP scope for
knowledge grounding.

## Context
- `cub/rag.py` is a separate experiment, not harness code; its OllamaEmbedder dim fix is a
  real bug catch but not necessarily the harness path.
- build-ref lists RAG as post-MVP. But agentic memory (auto `search_memory`/`add_memory`)
  is already enabled and may cover MVP needs.

## Resolution shape
Research findings + context pointer (branch `research/rag-scope`) recommending include/defer
and the seam if deferred.

================================================================================
TICKET D5 — Memory backend migration path  (label: wayfinder:task)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Define the seam from MVP `SqliteDb` + agentic memory to the post-MVP durable
PostgreSQL + pgvector backend (ADR 0010) that also supports durable scheduling. What interface
must `agno_agent.py` hide behind so the storage swap is non-breaking?

## Context
- Depends on D4's decision (include RAG now vs defer). If RAG deferred, the Seam is purely
  memory-store swap; if included, it also covers vector retrieval.
- ADR 0010 lists Postgres+pgvector post-MVP and durable scheduling.

## Resolution shape
A written seam/spec (interface boundary) recorded on the ticket; unblocks later migration work.

================================================================================
TICKET D6 — Observability in MVP  (label: wayfinder:task)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Does the MVP include any local tracing/observability (e.g. MLflow / Latitude local), or is all
observability post-MVP? The build-ref (#82) mentions observability but the MVP boundary is
unclear. Decide what minimal signal (if any) the harness emits locally.

## Context
- Local-first constraint: any tool must be self-hostable, no cloud egress.
- build-ref lists observability as a build item; MVP scope open.

## Resolution shape
A decision: include/none + which local tool, recorded on the ticket.

================================================================================
TICKET D7 — Connect MCP git-server  (label: wayfinder:task)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Wire the existing MCP git-server into the harness (build-ref #82). Shape depends on D2 (transport
+ adapter). Confirm the MCP server is available locally and define the tool-surface the harness
exposes for repo operations (read-only per `git * → deny` posture, unless explicitly granted).

## Context
- D2 fixes transport/adapter; MCP git-server connection is downstream of that.
- Current agent `gh`/git access is permission-gated — note the auth gap (see D10).

## Resolution shape
A decision + wiring plan recorded on the ticket; actual connection is a later build step.

================================================================================
TICKET D8 — `run_harness` safety policy  (label: wayfinder:grilling)  [RESOLVED — see Decisions so far]
================================================================================

## Question
`run_harness` is a shell-exec tool gated by `requires_confirmation=True` — powerful and
high-risk until an allowlist exists. Define the allowlist: repo-root confinement, no network
egress, permitted command patterns. This is the HITL policy for the most dangerous tool.

## Context
- `agno_agent.py` imports `cub.hooks` which enforces egress-deny for `EGRESS_TOOLS` +
  provenance logging. `run_harness` must sit within that policy.
- Until D8 lands, `run_harness` is treated as high-risk.

## Resolution shape
A concrete allowlist spec (command patterns, cwd, egress rules) on the ticket.

================================================================================
TICKET D9 — Verification & e2e  (label: wayfinder:task)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Define the MVP verification check: AgentOS endpoint answers via local Ollama; `approve_action`/
`run_harness` pause for HITL and continue after approval; serves on `:7777`. This is the
acceptance criteria for #82. Needs the RTX 4080 Fedora box (no `agno`/`ollama` in this env).

## Context
- Depends on D1 (HITL delivery) and D2 (transport).
- Current env cannot verify (no agno/ollama installed); validation requires target hardware.

## Resolution shape
A written test/acceptance procedure (commands + expected results) on the ticket.

================================================================================
TICKET D10 — Agent `gh`/wayfinder access  (label: wayfinder:task)  [RESOLVED — see Decisions so far]
================================================================================

## Question
Provision `gh` auth so the agent can read/create issues (currently permission-gated:
`gh * → ask`, `git * → deny`). Decide the credential scope (read vs write issues) and where
the token lives, consistent with local-first / zero-egress. This unblocks the agent's own
wayfinder/tracker participation.

## Context
- The charting of this very map was done as a local draft because `gh` was unauthenticated.
- Resolving this lets the agent self-manage tickets going forward.

## Resolution shape
A decision + credential-location note (no secret committed) on the ticket.
