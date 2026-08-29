---
title: Vercel Eve — öppen TS-agentramverk, men moln-ekosystem & språkbyte
date: 2026-08-27
status: draft
context: |
  SHALLOT = single-user, local-first Python-agent (PM/dev/research/cybersec/OT).
  Spårval #74 granskar Vercel Eve som plattformskandidat. Kriterier: Enkelhet >
  Kapabilitet > Anpassning; Fedora RTX 4080 16GB, lokal Ollama, PWA/Tailscale.
method: |
  Primärkällor: vercel.com/eve (produktsida), npm-metadata `eve` (registry.npmjs.org),
  GitHub-repo vercel/eve (README + källkod) och eve.dev/docs, hämtade 2026-08-27.
---

# Vercel Eve — primärkällegranskat 2026-08-27

Kandidat per issue #78. Trots Vercel-molyten: **öppen källkod (Apache-2.0)** och
körbar lokalt — men det är ett **TypeScript-ramverk i Vercel-AI-SDK-ekosystemet**,
inget self-host-turnkey och ingen lokalförst-plattform.

## 1. Vad det är (primärkällebevis)

- Produktsida: "The Agent Framework — Like Next.js for web apps, but for agents. **Markdown for instructions and skills, TypeScript for tools. Durable by default**." — vercel.com/eve.
- npm: `eve` 0.46.1 — "**Filesystem-first framework for durable backend AI agents that run anywhere**"; repo git+github.com/vercel/eve.git; keywords: agent-framework, durable, mcp, ai-sdk, nextjs, serverless, workflow, evals, observability, tools; deps nitro+undici — registry.npmjs.org/eve/latest.
- GitHub vercel/eve: aurörig authoring-interface — `agent.ts` (model+runtime-config), `instructions.md` (alltid-på systemprompt), `tools/` (typade funktioner) — README.
- License: **Apache-2.0** — LICENSE i repo.

## 2. OotB-koll (mot SHALLOT-kriterierna)

- **Kör-var som**: "**locally, on Vercel, or on a long-running Node.js host**" — produktsida. Durable by default: conversation/checkpoints vid steps, "parked work", per-session-minne via `defineState()` — eve.dev/docs.
- **Modeller/providers**: provider-neutral observability (egen OTel/v2-traces, "local observability" i repo research/provider-neutral-local-observability.md) men modeller skickas via AI SDK + **Vercel AI Gateway** (setup/provider-settings.ts). **Källkodssökning `ollama` i vercel/eve: 0 träffar** → lokala Ollama-modeller ej förstaklass; OpenAI/Anthropic/Google-providers i fokus.
- **MCP**: stöd (npm keyword mcp; provider-tools i src). **UI/dashboard**: inget — det är ett backend-ramverk; PWA/HITL-UI görs själv.

## 3. SHALLOT-passform (Enkelhet / Kapabilitet / Anpassning)

- **Enkelhet ★★☆☆☆**: hela harnesset (Python 3.12 + Pydantic AI, 7 verktyg, policy/HITL, SQLite-ledger) **måste skrivas om i TypeScript** — total migration, ingen befintlig-kod-återanvändning. Egen PWA, egen HITL-kö, egen pg-sidecar kvar att bygga.
- **Kapabilitet ★★★★☆**: ramverket är starkt (durable steps, workflows, evals, MCP, parked work) — men durable-modellen är **filesystem-first**, inte PostgreSQL+pgvector+Temporal som SHALLOT valt (ADR 0010). Ollama kräver egen AI-SDK-provider-konfig och går mot Vercel-ekosystemets AI Gateway-tänk.
- **Anpassning ★★☆☆☆**: möjligt att köra lokalt på Fedora och ansluta PWA, men varje SHALLOT-specifik krav (OT-vision, HITL-godkännanden, pgvector-episodiskt minne, Temporal-durable, SV/EN) byggs från grunden i ett annat språk, i ett ekosystem som pekar bort från lokalförst.

## 4. Slutsats

Eve är kapabelt och OSS, men **fel arkitektur för SHALLOT**: språkbyte till TS,
molntjänst-ekosystem (AI Gateway), filesystem-durable i stället för pg/Temporal och
inget förstklassigt Ollama. Kostnaden i anpassning överstiger allt ramverket ger.
**Avvisad som spår.** (Värt att hålla ögonen på om TS-vägen någonsin aktualiseras.)

## Sources (primary)

- https://vercel.com/eve (produktsida, hämtad 2026-08-27)
- https://registry.npmjs.org/eve/latest (npm-metadata 0.46.1)
- https://github.com/vercel/eve (README + LICENSE + src, hämtat 2026-08-27)
- https://eve.dev/docs (durable/memory/state)