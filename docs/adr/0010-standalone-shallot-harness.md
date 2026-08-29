---
status: accepted
---

# Fristående SHALLOT Harness med ACP och granskat långtidsminne

> **Reviderad 2026-08-27 (spårval #74, grilling #80/#81):** Agent-runtime-kärnan
> byts från egen Pydantic AI-harness till **Agno v3.0.x (AgentOS-runtime)** —
> FastAPI-API + SSE-streaming + sessions/persistence + inbyggd MCP-server +
> restart-safe HITL (workflows, state persistat i DB), nativ lokal Ollama,
> Postgres+pgvector. Motiv: harnesset fungerade inte, migrationskostnad ≈ 0,
> och Agno levererar ADR-målbilden (pgvector-minne, HITL, durable) ootb. Övrigt
> i detta ADR (lokalförst, modell-targets, budget, adaptrar, GitHub-tracker)
> står fast. Grund: docs/research/{turnkey-agent-platforms-2026,deepagents-
> langchain-2026,pydantic-harness-baseline}.md. Detta ersätter Pydantic+graph-
> beskrivningen i originalbeslutet nedan.
> **Beslut bekräftat av ägaren 2026-08-27.** Hermes Agent (Nous, MIT) övervägdes
> som mest-OOTB-kandidat men föll på pgvector-minne (plugin), python-reuse och
> autonomi-krocken med granskad promotion; Agno vinner på rätt arkitektur.

SHALLOT Harness byggs som en separat, fristående personlig agentplattform för projektledning, utveckling, forskning, cybersäkerhetsarbete och fysiska byggen. Den är inte Cub-agenten i OT-demon. Separationen hindrar att utvecklingsverktyg, personligt minne och breda behörigheter hamnar i den operativa OT-agentens trust boundary.

**Decision:** Python 3.12, **Agno v3.0.x (AgentOS) som agent-runtime-kärna** (FastAPI-API, SSE-streaming, sessions/persistence, MCP-server, durable HITL i workflows), PostgreSQL + pgvector som canonical state/minne/RAG, och Temporal som mål för schemaläggning, restart-safe HITL och flera workers. Fedora (RTX 4080 16GB VRAM, 64GB RAM) är kontrollnod; Mac och Fedora kan köra klienter/workers via privat Tailscale-nät. Rootless Podman begränsar verktyg. Lokal Ollama-inferens är default; GreenPT och Mistral EU är policy- och budgetstyrda cloud-adapters med högst €20/månad.

Harnesset exponerar samma kärna genom ACP v1 till Zed, AG-UI till webbgränssnittet och MCP till andra klienter. ACP/AG-UI/MCP är adapters, aldrig canonical state. GitHub Issues förblir canonical tracker; Craft-mappen SHALLOT är en asynkron operativ mirror där autonoma uppdateringar är tillåtna efter lyckad canonical uppdatering.

**Model targets (Ollama, Fedora RTX 4080 16GB VRAM):**

| Roll | Model | VRAM | Användning |
|------|-------|------|------------|
| Vision + Reasoning (default) | `ollama:ministral-3:8b` | ~6GB | Vision+tools+strukturerad output, 256K ctx, SV/EN, Apache-2.0 (Mistral track) |
| Vision (starkare general) | `ollama:qwen3-vl:8b` | ~6GB | Bäst generell hårdvarusyn i 16GB-klassen (OCR/spatial); sätt `VISION_MODEL=qwen3-vl:8b` |
| Reasoning (A/B-kedja) | `ollama:ministral-3:14b` | ~9GB | Endast vid `chain=true`; byter modell, passar 16GB sekventiellt |
| Cloud (policy-gated) | NIM Free (`nvila`) / OpenRouter Free (`qwen2.5-vl-7b`) | €0 | Endast ej känsliga bilder, opt-in i UI |

`mixtral:latest` (26GB Q4_0) **överskrider 16GB VRAM** och har ingen vision — används inte längre som default. `llava:13b` (legacy, 4K ctx) byts ut mot `ministral-3:8b`/`qwen3-vl:8b`. Single-model-kedja (vision+reasoning i samma VLM) är default; tvåmodellskedja endast för A/B. RAG-prompt (BOM/schema) ger störst ROI för wiring-validering. Validera tool-call/structured-output innan produktion (se forskning).

Minne delas i working, episodiskt, semantiskt och procedurt minne med separata `person:johannes`, `workspace:shallot` och session-namespaces. Strukturerade minnen har provenance, giltighet, sensitivity och TTL. Agenten får föreslå egna prompt-, skill- och runbook-ändringar men de aktiveras först efter mänskligt godkännande och regressionstest. `forget` skapar verifierbar retraction/deletion; modelloutput får aldrig direkt bli canonical fakta eller aktiv procedur.

**Considered Options:** LangGraph + Deep Agents gav starkast färdig checkpoint/time-travel men större framework-yta; en egen event-sourced Chronicle gav maximal kontroll men för mycket egen infrastruktur; Pydantic-stacken valdes för typning, befintlig kod, officiell ACP/AG-UI/durable-execution-integration och lägre migrationskostnad.

**Consequences:** Första leveransen kör en worker men använder permanenta egna scheman och seams som kan flyttas till Temporal-workers. Pydantic Harness ACP är experimentell och måste isoleras bakom kontraktstest och raw ACP SDK-fallback. Cub-ADR 0005–0007 supersedas inte; de gäller Cub och behöver separat aktualitetsgranskning innan operativ implementation.

Research: `docs/research/standalone-agent-harness-stack-2026.md` och `docs/research/acp-and-model-providers-2026.md`.
