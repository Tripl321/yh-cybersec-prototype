---
title: Hermes Agent (Nous Research) — autonomt agent-ramverk för SHALLOT
date: 2026-08-27
status: draft
context: |
  SHALLOT = single-user, local-first AI-agent (PM/dev/research/cybersec/OT).
  Spårval #74: from-scratch vs turnkey vs ramverk. Rädering av tidigare
  fordon: forskning #77 gällde enligt ägaren "hermes agent" = Nous Research
  Hermes Agent-ramverk (inte Nous-Hermes-modellfamiljen). Detta dokument
  granskar rätt objekt med primärkällor. Kriterier: Enkelhet > Kapabilitet >
  Anpassning; Fedora RTX 4080 16GB, lokal Ollama, PWA via Tailscale.
method: |
  Primärkällor: github.com/NousResearch/hermes-agent (README + releases, via
  GitHub-API), official docs hermes-agent.nousresearch.com/docs (llms.txt +
  sidor för api-server, dashboard, memory-providers, security, providers),
  hermes-agent.ai, hämtade 2026-08-27. Version: v0.20.5 (2026-08-19).
---

# Hermes Agent (Nous Research) — primärkällegranskat 2026-08-27

Kandidat per issue #77. **Autonomt agent-ramverk från Nous Research** — inte
modellfamiljen Nous-Hermes (tidigare research, nu tillbakadragen).

## 1. Vad det är (primärkällebevis)

- Repo: NousResearch/hermes-agent, "The agent that grows with you", **MIT**, skapat 2025-07-22, **237K stjärnor** (GitHub-API). Install: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash` (Linux/macOS/WSL2/Termux) — README Quick Install.
- Release: v0.20.5 (v2026.8.19) — rollar ~323 merged PRs; aktiv 0.x, snabb cadence (crux för produktion).
- Position: "terminal-native autonomous coding and task agent with persistent memory, agent-created skills, and a messaging gateway ... 21+ messaging platforms ... Runs on local, Docker, SSH, Daytona, Modal, or Singularity backends" — docs llms.txt intro.

## 2. OotB-koll (mot SHALLOT-kriterierna)

- **Lokala modeller / Ollama**: providers-dok: "Ollama and vLLM ... to advanced routing and fallback configurations"; "local daemon — no key needed on loopback". Plus Nous Portal / OpenRouter / OpenAI / Anthropic / Google / **alla OpenAI-kompatibla endpoints** — docs integrations/providers, README ("Use any model you want — switch with `hermes model`, no lock-in").
- **API / custom-frontend**: **OpenAI-kompatibel API-server** — "Point any OpenAI-compatible client at [..]" / "connect Open WebUI, LobeChat, or any other frontend"; stödjer Chat Completions + Responses API med server-side state — docs user-guide/features/api-server.
- **Dashboard/UI**: **Hermes web-dashboard** med plugin-system ("palettes, typography, ... API routes") — docs features/extending-the-dashboard. Desktop (macOS/Windows), TUI, CLI, messaging — README.
- **HITL/approvals**: 8-lagers säkerhetsmodell inkl **Dangerous Command Approval** + **Approval Modes** + user authorization + container isolation — docs user-guide/security.
- **Minne**: closed learning loop; agent-curated memory, **FTS5-sessionsökning + LLM-summering**, autonomous skill-creation; **memory-provider-plugins: Honcho, OpenViking, Mem0, Hindsight, Holographic** — README + docs features/memory(-providers). Ej native pgvector (kräver plugin, t.ex. Mem0 med postgres).
- **Autonomi/durable**: cron-jobb, GitHub-workflows, profiles/sessions, provider-routing + fallback-providers + credential-pools — hermes-agent.ai + docs features.

## 3. SHALLOT-passform (Enkelhet / Kapabilitet / Anpassning)

- **Enkelhet ★★★★☆**: mest komplett OOTB av alla kandidater — egen web-dashboard, approvals, minne, cron, messaging, lokal Ollama, en-rads-install, MIT. Men: ramverkets egen paradigm (autonomt lärande, auto-skapade skills) kräver styrning för att matcha ADR:s granskade promotion; 0.x-cadence → churn.
- **Kapabilitet ★★★★☆**: bredast verktygs-/skill-ekosystem + MCP/ACP + OpenAI-kompatibel API + vision-väg via multimodal providers (MiniMax-partnerskap; lokal Ollama VLM via OpenAI-kompatibla bild-meddelanden — bör verifieras). Undantag: memory inte pgvector-native; durable är cron/sessions, ej Temporal.
- **Anpassning ★★★☆☆**: lokal Ollama + egen frontend via OpenAI-kompatibel API eller dashboard-plugins. Men egna OT-verktyg flyttas in i dess toolset/skill-system (nytt paradigm), och dashboard är "deras" (plugins/API-routes ger viss kontroll). HITL-approvals finns men är designade kring dess CLI/gateway-flöde.

## 4. Slutsats

Hermes Agent är nu den **starkaste turnkey-liknande kandidaten**: mest färdigt
OOTB (dashboard + approvals + minne + lokal Ollama + MIT) med egent underminerad
custom-PWA (OpenAI-kompatibel API-server). Väger mot Agno: Hermes har
**mer färdigbyggt**, Agno har **rätt arkitektur** (pgvector-native minne, Python-
tools återanvänds, durable-HITL i DB, custom PWA helt fri) och mindre yta.
Avgörandet = hur mycket av "brains" som ska vara färdigbyggt vs hur mycket vi
styr själva (kräsna på autonomi/lärande + pgvector + stack-kontroll → Agno vinner;
max OOTB och acceptabel inlåsning i ramverksparadigm → Hermes Agent).
Detta ersätter/upphäver tidigare "hermes-nous-model-2026.md".

## Sources (primary)

- https://github.com/NousResearch/hermes-agent (+ GitHub-API metadata/releases)
- https://hermes-agent.nousresearch.com/docs (llms.txt; features/api-server, features/extending-the-dashboard, features/memory-providers, user-guide/security, integrations/providers)
- https://hermes-agent.ai (cron/messaging/cloud-eller-self-host)