---
title: Nuvarande Pydantic AI-harness — baslinje för spårvalet
date: 2026-08-27
status: draft
context: |
  SHALLOT = single-user, local-first Python-agent. Spårval #74: from-scratch vs
  turnkey vs ramverk. Föreliggande dokument kartlägger dagens from-scratch-harnas
  verkliga kapabilitet och huvudvärk som de andra spåren mäts mot. Grund:
  ADR 0010 + kod i agent/src/shallot_harness.
method: |
  Lokala primärkällor, lästa 2026-08-27: docs/adr/0010-standalone-shallot-harness.md,
  agent/pyproject.toml, agent/src/shallot_harness/{harness,agent,server,policy,
  store,memory}.py.
---

# Pydantic AI-harness-baslinje (from-scratch spår)

## 1. Vad som finns idag (kod + ADR)

- **Stack** (ADR 0010, agent/pyproject.toml): Python 3.12, `pydantic-ai-slim[ollama]>=0.3,<1` (kod kommenterar 0.8.1), FastAPI+uvicorn, `mcp>=1.0`. Event-store: append-only (SQLite nu, "PostgreSQL adds pgvector; this stays clean" — store.py).
- **Arkitektur** (ADR 0010): explicit `pydantic-graph`-flöden, PostgreSQL+pgvector som canonical state/minne/RAG (mål), Temporal för schemaläggning/restart-safe-HITL/workers (mål). ACP v1 (Zed), AG-UI (webb), MCP (klienter) — alla bara adapters; GitHub Issues canonical tracker.
- **Agent** (agent.py): `Agent(model=DEFAULT_MODEL, ...)`, default `"openai:ministral-3:8b-instruct-2512-q4_K_M"`; verktyg bl.a. `search_memory`, `add_memory` (namespaces working/episodic/...), `approve_action`, `get_budget_status` (7 total); hård systemprompt mot proaktiv verktygsanvändning.
- **HITL**: policy.py = idempotent `PolicyGate` (approval-actions, budgetlimits), `ApprovalRequired` med action_id, `approve_action`-verktyg.
- **Streaming/server**: server.py = **hembyggd SSE** med verktygsutdrag, truncate, `_pending_approvals`; kommentar: "pydantic-ai 0.8.1 har inget nativt Ollama; route genom Ollamas OpenAI-kompatibla /v1" — modellen läses som `openai:*` mot `localhost:11434/v1`.

## 2. Kapabilitet / Enkelhet / Anpassning idag

- **Kapabilitet ★★★★☆**: chat + 7 verktyg + vision (ministral-3:8b VLM, qwen3-vl:8b alt) + HITL-godkännanden + SSE-streaming + (episodiskt) minne. ADR:s pgvector-RAG, Temporal-durable och AG-UI/ACP/MCP-lager är **beslutade mål, delvis ostubbade** (stub_reasoner.py, _otel_events_stub.py).
- **Enkelhet ★★★☆☆**: inget lag utanpå (ingen migrationskostnad), men egenhändigt infrastruktur-grus: hembyggd SSE-server (ej AG-UI), OpenAI-kompatibel Ollama-route (0.8.1-quirk), SQLite-ledger med design-lucket till pgvector, single worker (ingen durable).
- **Anpassning ★★★★★**: 100% lokalförst, lokal Ollama förstklassig, OT-vision-verktyg redan på plats, custom PWA-dashboard byggs fritt, ACP/AG-UI/MCP-adaptrar kontrollerade av oss.

## 3. Huvudvärk (verifierade ur kod)

1. **Ollama-routing**: 0.8.1 saknade nativ provider → OpenAI-/v1-hack gör model-strängar (`openai:ministral...`) och endpoint-hantering till custom-logik innan nästa major-nytta av nativ `ollama:`-provider.
2. **Hembyggd SSE/streaming** (server.py) → och AG-UI-vägen kräver att vi själva byter/repar, ingen plattform som levererar stream+approval-kort-protokollet.
3. **Ingen durable execution**: en worker, approval-kön i minne/ledger utan restart-skydd; Temporal fast beslutat men inte byggt.
4. **Minne/RAG på SQLite**: episodiskt minne saknar pgvector-semantik; RAG-BOM/schema-ROI (ADR) outnyttjat.
5. **Stubbar**: reasoner/OTel stubbade → observability/instrumentering saknas. (Endpoint-oberoende användning utöver vårt eget.)

## 4. Slutsats

From-scratch-spåret är **redan längst fram på anpassning och lokalförst**, med verklig kapabilitet i dag; dess kostnad är hemmabyggd infra (SSE/Ollama-route/durable) som motsvarar det Agno/Deep-Agents levererar paketerat. Det är exakt denna gap-mätning som gör att turnkey-ramverk övervägs (#75 → Agno) och talar för att **behålla harness men kura sin infra-huvudvärk** — snarare än att byta spår.

## Sources (primary)

- docs/adr/0010-standalone-shallot-harness.md
- agent/pyproject.toml
- agent/src/shallot_harness/{harness,agent,server,policy,store,memory}.py