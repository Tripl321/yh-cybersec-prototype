---
title: Deep Agents (LangChain) — lätt Python-agentramverk för SHALLOT
date: 2026-08-27
status: draft
context: |
  SHALLOT = single-user, local-first, privacy-sensitive AI-agent (PM / dev /
  research / cybersec / OT-hårdvara), idag handrullad Pydantic AI-harness.
  Spårval #74: from-scratch vs turnkey vs ramverk. Detta dokument granskar
  LangChain Deep Agents som ramverkskandidat. Kriterier: Enkelhet > Kapabilitet
  > Anpassning; Fedora RTX 4080 16GB, lokal Ollama, PWA via Tailscale.
method: |
  Primärkällor: officiell GitHub-README (langchain-ai/deepagents) och officiella
  docs (docs.langchain.com/oss/python/deepagents) hämtade 2026-08-27 och
  sektions-matchade. Version: python-paketet `deepagents`.
---

# Deep Agents (LangChain) — primärkällegranskat 2026-08-27

Kandidat per issue #76. Ett importerbart Python-paket byggt OVANpå LangGraph,
inte en plattform.

## 1. Vad det är (primärkällebevis)

- Paket: `deepagents` (PyPI, `uv add deepagents`); entrypoint `create_deep_agent(model=..., tools=[...], system_prompt=...)` — github.com/langchain-ai/deepagents#quickstart.
- Läger: "LangGraph är graf-routern, LangChains `create_agent` är minimal harness ovanpå, Deep Agents är en mer opinionated harness ovanpå `create_agent`" — samma byggblock, med **filsystem, sub-agents, context management och skills inbyggda** — README FAQ.
- Produktion: byggt på LangGraph; tracing/eval/monitoring via **LangSmith**; full guide i docs/going-to-production — README FAQ.

## 2. OotB-koll (mot SHALLOT-kriterierna)

- **Lokala modeller / Ollama**: "Any model that supports tool calling — frontier API:er, open-weight hos Baseten/Fireworks, **self-hosted via Ollama, vLLM eller llama.cpp**" — README FAQ. Exempel i officiell docs: `model="ollama:north-mini-code-1.0"` — docs overview Quickstart.
- **Plan / delegation**: inneboende **task planning + subagents** — docs overview §Delegation.
- **Verktyg och filsystem**: typed tools, MCP, virtual filesystem med permissions, kod-execution— docs overview §Execution environment.
- **HITL**: LangGraph **interrupts** via parametern `interrupt_on={"edit_file": True}` — pausar före känsliga tool-calls, människa kan godkänna/ändra input — docs overview §Human-in-the-loop.
- **Context / minne**: skills (lazy-loadade), **memory = AGENTS.md-filer** (`memory`-parameter) lagrade i State/Store/FilesystemBackend, summarization/context offloading, prompt caching — docs overview §Context management. OBS: ingen pgvector-RAG-semantik i Deep Agents själv.
- **Streaming**: stöds (docs §Streaming). **Durable**: via LangGraph checkpointers/sömn-mekanismer — för SaaS-rekommenderat via **LangSmith Deployments** (managed infra, docs going-to-production), men kan köras själv med egen checkpointer-backend.

## 3. SHALLOT-passform (Enkelhet / Kapabilitet / Anpassning)

- **Enkelhet ★★★☆☆**: Python, samma språk som nuvarande harness → delvis migration. Men större framework-yta (LangGraph + create_agent + Deep Agents lager) — ADR 0010 klassade redan "LangGraph + Deep Agents = större framework-yta". Filsystem/subagents/context-minne får vi gratis, men egen SSE/AG-UI + HITL-upplevelse och pgvector-RAG byggs ändå.
- **Kapabilitet ★★★★☆**: starkast plan/verktyg/HITL av kandidaterna; MCP; filsystem. Minne är dock AGENTS.md-filorienterat, inte episodiskt pgvector — SHALLOTs episodiska/semantiska minne kräver egen Postgres-lagring oavsett. Durable kräver antingen LangSmith (cloud) eller egen checkpointer (Postgres) — Temporal-schemat kvar som custom.
- **Anpassning ★★★★☆**: Python-native, Ollama förstklassig, egen PWA fullt möjlig (tunna adaptrar). OT-vision via multimodal chat-modell (t.ex. qwen3-vl via Ollama) fungerar. Vinsten kontra from-scratch: plockar bort egen plan/skill/subagent-plumbing.

## 4. Slutsats

Deep Agents är den **starkaste ramverkskandidaten** (Python, lokal Ollama, HITL-interrupts, MCP) och bekräftar/stärker ADR 0010:s avvägning. Det vinner på kapabilitet men kostar framework-yta och lämnar pgvector-minne + Temporalscheman + PWA/AG-UI kvar att bygga själv — alltså ett delsteg mot from-scratch, inte en destination.

## Sources (primary)

- https://github.com/langchain-ai/deepagents (README, hämtad 2026-08-27)
- https://docs.langchain.com/oss/python/deepagents/overview
- https://docs.langchain.com/oss/python/deepagents/going-to-production