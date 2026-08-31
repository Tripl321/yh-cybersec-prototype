# Research: D4 — RAG / Knowledge Inclusion in SHALLOT Harness MVP

- **Ticket:** D4 (wayfinder, `wayfinder/harness-mvp-map.md` #95)
- **Type:** research (AFK, no human-in-the-loop)
- **Date:** 2026-08-31
- **Branch pointer (per ticket shape):** `research/rag-scope`
- **Sources:** repo (`agno_agent.py`, `cub/rag.py`, `docs/architecture/agno-mvp-build.md`, ADR 0010, ADR 0006); primary Agno docs (docs.agno.com: `/memory/agent/overview`, `/memory/overview`, `/knowledge/agents/overview`, `/knowledge/concepts/search-and-retrieval/overview`).

---

## RECOMMENDATION

**DEFER explicit RAG (Agno `Knowledge` base + vector store over the SHALLOT doc corpus) to the Postgres+pgvector backend (ticket D5).** Do NOT add a vector/RAG path in the MVP.

This is consistent with the build-ref, which lists RAG/knowledge as POST-MVP (`docs/architecture/agno-mvp-build.md:60`, `:197`). The MVP's grounding need is already met deterministically, and `enable_agentic_memory=True` does **not** cover doc retrieval — it is a different capability.

---

## WHAT AGENTIC MEMORY ACTUALLY COVERS (vs RAG)

`agno_agent.py:125` sets `enable_agentic_memory=True`. Per primary Agno docs this supplies the agent a tool to **manage user/operator-level memories** — "What do you know about me?" (preferences, facts, context learned from conversation), persisted in the agent DB and re-injected into context across runs (docs.agno.com `/memory/agent/overview`, `/memory/overview`, `/examples/basics/agent-with-memory`).

- It is **not** a corpus index. It does not embed, chunk, or similarity-search project docs (ADRs, specs, NIST CSF, etc.).
- It is **orthogonal to RAG**: agentic memory = operator facts; RAG/knowledge = domain document retrieval.
- The build-ref lists `search_memory`/`add_memory` as agentic-memory tools (`agno-mvp-build.md:55`); these operate on the operator, not the doc set.

Conclusion: having agentic memory ON does **not** satisfy "ground the agent on SHALLOT project docs." That grounding currently happens through a separate mechanism (below).

## HOW THE MVP ALREADY GROUNDS ON DOCS

`agno_agent.py` grounds on SHALLOT docs via **three custom file-reading tools**, not via RAG:

- `get_project_state` (`:58`) — reads ADRs, spec, dev log, registry, budget.
- `get_event_history` (`:75`) — dev log chronology.
- `get_budget_status` (`:81`) — budget from `CONTEXT.md`.

These are deterministic, zero-egress, local-first, require no embedder, and directly satisfy the system prompt's "Ground decisions in the project's own docs" (`agno_agent.py:40`). For the *small* SHALLOT doc set (a handful of ADRs/specs), whole-document reads are cheaper and more faithful than embedding+retrieval.

## ASSESSMENT OF `cub/rag.py`

`cub/rag.py` is a **separate local experiment** for the Cub agent (LanceDB + `SentenceTransformerReranker` + `OllamaEmbedder` dims=768, hybrid search). It is NOT harness code and is explicitly flagged as an "alternative inference path until the framework choice is reconciled" (ADR 0005/0006 conflict, `cub/rag.py:14`).

- Its `OllamaEmbedder` dim=768 fix is a real bug catch but belongs to Cub's stack, not the harness.
- Adopting its LanceDB pattern in the harness now would create a **second, divergent vector path** that D5's Postgres+pgvector migration would have to replace anyway — wasted work and a forked backend.
- **Out of scope for the MVP harness.** Relevant only as a reference pattern for the later Cub RAG work, not as a D4 decision input for SHALLOT Harness.

## WEIGHING LOCAL-FIRST / ZERO-EGRESS (ADR 0006)

Both Agno agentic memory and an Agno `Knowledge` base *can* be local (Sqlite/LanceDB vector, local Ollama embedder) — neither forces egress. So zero-egress does **not** argue for adding RAG now; it only constrains the *future* backend choice (which D5 already fixes as local Postgres+pgvector). The MVP grounding via file reads is the most strongly zero-egress option of all (no model, no vector store, no embedder at all).

---

## THE SEAM (so D5 swap is non-breaking)

If RAG is deferred, the only thing D5 must later replace is **where the doc text comes from**. Make that access go through one internal boundary now, so the tool contract the agent sees never changes.

1. **Add a single loader module** (e.g. `harness/knowledge.py` or `shallot_knowledge.py`):
   - Exposes the doc-source list and a `load_project_knowledge() -> str` (and/or `load_event_history()` / `load_budget()`) used by `get_project_state` / `get_event_history` / `get_budget_status`.
   - Today its body is a `Path.read_text()` over `REPO/"docs/..."` (zero-egress, no embeddings) — i.e. it wraps the existing `_read()` calls.

2. **Refactor the three tools** in `agno_agent.py` to call the seam instead of hardcoding `REPO/"docs/..."` paths. Tool names, args, and return shape stay identical — the agent's observable behavior is unchanged.

3. **D5 migration** then only swaps the loader's internals: behind the same function signature, return grounded text from an Agno `Knowledge` object backed by Postgres+pgvector (and optionally register a `search_knowledge_base` tool). No change to tool contracts or system prompt.

4. **Leave `enable_agentic_memory=True` as-is.** It is operator memory, not RAG; it is correct to keep for MVP and is independent of this seam.

This satisfies the ticket's requirement: "the seam if deferred" is the **doc-access loader boundary**, making D5's storage swap purely internal/non-breaking.

---

## DECISION TO RECORD ON TICKET D4

> **DEFER RAG to Postgres+pgvector (D5).** Agentic memory (`enable_agentic_memory=True`) covers operator facts only, not doc grounding; MVP grounding is already done deterministically by `get_project_state`/`get_event_history`/`get_budget_status` file-read tools (zero-egress, no embedder). `cub/rag.py` is a separate Cub experiment — out of scope. Seam: wrap doc-source access behind a single loader module (`harness/knowledge.py`) that the three grounding tools call; D5 swaps only the loader internals to an Agno `Knowledge`/pgvector backend behind the same signature — non-breaking.
