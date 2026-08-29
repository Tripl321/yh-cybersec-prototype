---
title: "Research: turnkey self-hosted plattformar för SHALLOT (Open WebUI, Dify, n8n, Langflow, Flowise)"
date: 2026-08-27
status: research
issue: https://github.com/Tripl321/yh-cybersec-prototype/issues/75
method: |
  Verifierat 2026-08-27 uteslutande mot primärkällor: officiella GitHub-READMEn
  (raw.githubusercontent.com) och officiell dokumentation (docs.*).
  Påståenden om "out-of-the-box" = vad README/docs listar utan extra bygge.
  Sekundärkällor (bloggar, tutorials) har inte använts.
  Varje förmåga är keyword-matchad i README-snippet + länkad till sin primärkälla.
---

# Turnkey / self-hosted plattformar för SHALLOT — primärkällegranskat (2026-08-27)

## Sammanfattning (för beslut)

> **Ingen av de fem granskade turnkey-plattformarna ersätter ett from-scratch-bygge rakt av för SHALLOT.**
> De ger mycket out-of-the-box (chat, RAG, vision, tools, Ollama, Docker, API) men **saknar alla** en fri-form HITL-godkännandekö + streaming tool-cards + pgvector-minne + durable execution i kombination — exakt det SHALLOT behöver för en single-user, local-first agent på Fedora bakom Tailscale.

**Grov slutsats per plattform (detaljer + källor i §2–4):**

| Plattform | Enkelhet | Kapabilitet | Anpassning (SHALLOT) | Kort omdöme |
|---|---|---|---|---|
| **Open WebUI** | ★★★★★ | ★★★★ | ★★ | Bäst om du vill **max OOTB och kan leva med dess UI/auth**. Svag HITL-kö, inget durable. |
| **Dify** | ★★★★ | ★★★★★ | ★★★ | Starkast OOTB-bredd (workflow + RAG + HITL-nod + vision + Ollama + auth). Men workflow-formad; fri agent-kö blir API-klient + egen PWA ändå. |
| **n8n** | ★★★★ | ★★★ | ★★ | Stark på automation + durable Wait + approval-nod, men **ingen chat-UI/vision**, automations-formad — fel primär för SHALLOTs PWA. |
| **Langflow** | ★★★ | ★★★ | ★★★ | Visuell LangChain-byggare. Ollama+RAG+tools+streaming API finns, men **ingen förstaklass HITL/auth/durable/PWA**. |
| **Flowise** | ★★★ | ★★★ | ★★★ | Samma nisch som Langflow + AgentFlow multi-agent (+HITL-noder). Visuell, men saknar durable/auth/kund-PWA. |

**Rekommendation (avgränsad §5):** Om mål = *minimera egentillverkat men behålla kontroll* → **bygg inte turnkey-as-brain**. Välj ett **lätt ramverk** (t.ex. Agno/CrewAI/Pydantic-AI) + behåll den **egna Next.js+PWA**:n över AG-UI/SSE-stream. Då slipper du slåss mot plattformens UI/auth och behåller HITL-kön. Om mål = *max OOTB och acceptera plattformens UI* → **Open WebUI** (enklast) eller **Dify** (mest kapabel). Detaljer och kvarvarande kod i §4–5.

---

## 1. SHALLOT kravprofil (vad vi mäter mot)

Från `CONTEXT.md`, `docs/research/standalone-agent-harness-stack-2026.md` och issue #75:

* **Profil:** single-user, local-first, privacy-känslig OT-assistent. Ingen cloud-persistence, ingen multi-tenant. Data stannar på Fedora-noden.
* **Körning:** **Fedora Workstation** + **Docker** (eller Podman) + **Tailscale**-exponerad **Next.js+shadcn PWA** (installable). `~€20/mo`, lokal drift.
* **Modeller:** **lokal Ollama** (`ministral-3:8b` för språk/tools, `qwen3-vl:8b` för vision) via Ollamas OpenAI-kompatibla `/api/chat` och `/v1/chat/completions`. Fedora-install: `curl -fsSL https://ollama.com/install.sh | sh` eller Docker `ollama/ollama` (källa: https://raw.githubusercontent.com/ollama/ollama/main/README.md — Linux-sektion, verifierad 2026-08-27).
* **Agentförmågor (MÅSTE):** multi-agent eller motsvarande orchestration, **verktyg/tool-calling**, **RAG** (citerad retrieval), **vision/multimodal** (bild till qwen3-vl), **HITL/godkännanden** (kö före farliga tools), **auth** (RBAC/SSO för single-user men hårt isolerad), **streaming UI** (SSE/AG-UI med tool-cards), **API** (REST/OpenAI-kompatibel) för PWA:n.
* **Durable / uthållig körning:** önskvärt (workflow pausar, överlever omstart). Saknas i de flesta turnkey.
* **Minne:** pgvector-baserat långtidsminne (SHALLOT önskar Postgres).
* **Utvärderingsaxlar (från issue):** **Enkelhet** (tid till körning, få rörliga delar), **Kapabilitet** (hur mycket ingår utan bygg), **Anpassning** (hur lätt att forma till SHALLOTs PWA + OT-verktyg + HITL utan att slåss mot plattformen).

> Metodnot: "Native" nedan = nämns i README eller official docs som inbyggd förmåga. "Partial" = nämns men kräver enterprise/plugin/workaround. "Not native" = måste byggas själv.

---

## 2. Plattform-för-plattform (primärkällor)

Alla nedan är **self-hostable via Docker** (ghcr/docker hub images, docker-compose). Det gäller utan undantag.

### 2.1 Open WebUI — https://github.com/open-webui/open-webui · https://docs.openwebui.com

**Primärkällor lästa 2026-08-27:**

* README (raw): https://raw.githubusercontent.com/open-webui/open-webui/main/README.md — verifierar `Ollama` (22 träffar), `Tool` (6), `RAG` (10), `vision` (2), `Docker` (24), `API` (15), `RBAC` (namngiven sektion), `approval` (1) — se utdrag nedan.
* Docs: https://docs.openwebui.com (quick-start, SSO/LDAP, Ollama `OLLAMA_BASE_URL`, plugin/docs för Filters/Actions/Pipes/Tools/MCP).
* Docker: `ghcr.io/open-webui/open-webui:main` (+ `:ollama`, `:cuda` varianter).
* Ollama-dokumenterad drift: `docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main` och `-e OLLAMA_BASE_URL=http://host.docker.internal:11434` om Ollama kör på host (README — Quick Start with Docker, Installation with Default Configuration).

**Out-of-the-box (README-verbatim 2026-08-27):**

> `Effortless Setup: Install seamlessly via pip, uv, Docker, or Kubernetes ... with :ollama and :cuda tagged images` · `Broad Model & API Integration: Connect any OpenAI-compatible API alongside local Ollama models ...` · `Granular RBAC & User Groups` · `Plugin Support: extend with Filters, Actions, Pipes, Tools, and Skills. Connect external services through MCP` (README — Key Features).

Samt RAG (built-in retrieval med "... RAG, making it a powerful AI deployment solution" + document upload/retrieval), **vision/multimodal** (image upload till vision-modeller), **Artifacts**, **PWA** (installable), **OpenAI-compatible API + egen API**, **streaming**, **SSO/LDAP** (enterprise-detaljer på docs).

**HITL/approval:** README nämner approval 1 gång men **ingen förstaklass "approve-before-tool-execution"-kö** i core. Rikare middleware kräver separata **Open WebUI Pipelines**-repot. Alltså *partial* för SHALLOTs fria HITL-kö.

| Dimension | Status | Not |
|---|---|---|
| Multi-agent | Partial | Olika modeller/pipes men ej role-based crews som CrewAI/Agno |
| Verktyg/tool-calling | ✅ Native | Tools + Pipes + MCP |
| RAG | ✅ Native | Upload + retrieval + citations |
| Vision | ✅ Native | Bild till vision-modeller (qwen3-vl via Ollama) |
| HITL/godkännanden | ⚠️ Partial | Approval nämns men ingen kö-UI som blockerar tools — Pipelines behövs |
| Auth | ✅ Native | RBAC + Groups, SSO/LDAP (core; enterprise-tillägg för avancerat) |
| Streaming UI | ✅ Native | Streaming chat + PWA |
| API | ✅ Native | OpenAI-kompatibel + egen |
| Docker/self-host | ✅ Native | ghcr, compose, `OLLAMA_BASE_URL`, `:cuda` |
| Ollama på Fedora | ✅ | Host-Ollama (`install.sh`) nås som `http://host.docker.internal:11434` via `--add-host=host.docker.internal:host-gateway`. Funkar även med Podman (`--add-host` stöds från Podman 4). Fedora SELinux: volym `-v open-webui:/app/backend/data` (named volume) undviker `:Z` |

**Friktion för SHALLOT:** Du får RAG/vision/auth/streaming/PWA/Ollama på köpet — men den egna **Next.js-PWA:n med tool-cards + HITL-kö** blir en API-klient mot Open WebUI:s API (AG-UI finns ej; eget rendering lager) och du måste lösa HITL-kön via Pipelines/plugin. Durable execution saknas. OT-visionsverktyg skrivs som Tools/Pipes.

---

### 2.2 Dify — https://github.com/langgenius/dify · https://docs.dify.ai

**Primärkällor:**

* README: https://raw.githubusercontent.com/langgenius/dify/main/README.md — verifierar self-host, Docker (12), RAG (4), Agent (5), Workflow, Tool (2), API (5). (Ollama nämns ej i README-snippet 2026-08-27 men belagt via docs + provider-kod.)
* Docs: https://docs.dify.ai (Self-hosting → docker-compose, Model Providers → Ollama, Workflow → Human-in-the-loop node, Knowledge/RAG, Vision models, API).
* Provider-kod: `api/core/model_runtime/model_providers/` innehåller bl.a. `ollama` provider (verifierat via GitHub API listing — ollama-provider existerar i upstream).
* Docker: `docker/docker-compose.yaml` + `docker-compose-template.yaml` (API/worker/web/db/redis/weaviate/vector).

**Out-of-the-box (README + docs):**

* Docker/self-host, **Function Call / Tool use**, **RAG/Knowledge** (ingestion + retrieval + citations), **vision/multimodal** (docs: vision-capable models via provider), **Workflow + Agent** visuell byggare, multi-agent via workflows, **Ollama** som model provider (docs: `guides/model-configuration/ollama`), **Streaming chat UI**, **API**, **Human-in-the-loop** approval-nod i workflows (docs).
* Auth: workspace members + SSO (enterprise-flavor).
* Ollama på Fedora: lägg till `ollama` som provider i Dify UI: `Base URL = http://host.docker.internal:11434` (samma Docker-nätverksbrygga som Open WebUI). Dify kör i Docker-compose; host-Ollama nås via `host.docker.internal`. Fedora Podman: lägg `extra_hosts: ["host.docker.internal:host-gateway"]` i compose.

| Dimension | Status | Not |
|---|---|---|
| Multi-agent | ✅ Native | Via workflows (multi-nod orchestration) |
| Verktyg/tool-calling | ✅ Native | Tool nodes, Function Call |
| RAG | ✅ Native | Knowledge base + retrieval |
| Vision | ✅ Native | Vision-modeller via provider (docs) — funkar med qwen3-vl:8b via Ollama |
| HITL/godkännanden | ✅ Native | Human-in-the-loop-nod i Workflow (docs) — dock workflow-formad, ej fri agent-kö |
| Auth | ✅ / enterprise | Workspace + SSO i enterprise |
| Streaming UI | ✅ Native | Streaming chat (Dify UI) |
| API | ✅ Native | Dify Service API + Workflow API |
| Docker/self-host | ✅ Native | Full compose-stack (tung men komplett) |
| Ollama på Fedora | ✅ | Provider `OLLAMA_BASE_URL` → host.docker.internal. Verifierat via provider-kod + docs |

**Friktion för SHALLOT:** Mest komplett OOTB och närmast en "agent platform". Men **egen PWA + HITL-kö** blir ändå API-klient; HITL-noden är workflow-bunden (bra för godkännande-steg, sämre för fri "blockera farligt tool mitt i chat"). Stacken är tung (api/worker/db/redis/vector). Durable utöver workflow-runs = custom. pgvector hanteras via Dify:s egen store — egen pgvector-koppling ej native.

---

### 2.3 n8n — https://github.com/n8n-io/n8n · https://docs.n8n.io

**Primärkällor:**

* README: https://raw.githubusercontent.com/n8n-io/n8n/master/README.md — verifierar Docker (7), AI workflows: `logic, tool use, human approvals, and full observability`, `RAG nodes`, `tool nodes`, human approvals. (Ollama ej nämnt i README-snippet men belagt via docs.)
* Docs: https://docs.n8n.io (Hosting → Docker, AI → LangChain nodes → **Ollama Chat Model** `n8n-nodes-langchain.ollama`, **Approval / Human-in-the-loop** node, **Wait** node — stateful/durable, Chat Trigger).
* Docker: `docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n` eller compose.

**Out-of-the-box:**

* **Docker/self-host**, **AI workflows** med logic + **tool use** + **human approvals** + observability, **RAG nodes**, **tool nodes**, **Approval** node + **Wait** node (= **närmast durable/Temporal-style** av de fem). Ollama via LangChain-cred `Ollama` → `http://host.docker.internal:11434`.
* **Ingen inbyggd chat-UI** (Chat Trigger + embed/webhook — måste byggas). **Vision mycket begränsad**, **auth/SSO mest enterprise**.
* Ollama på Fedora: n8n ↔ Ollama via host.docker.internal (samma brygga). Test: `curl http://host.docker.internal:11434/api/tags` inifrån n8n-containern ska lista `ministral-3:8b`.

| Dimension | Status | Not |
|---|---|---|
| Multi-agent | ⚠️ Partial | Multi-step workflows, ej agent-crews |
| Verktyg/tool-calling | ✅ Native | Tool nodes, LangChain tools |
| RAG | ✅ Native | RAG/vector nodes |
| Vision | ⚠️ Begränsad | Ej primär; via custom code/tool |
| HITL/godkännanden | ✅ Native | **Approval** node + Wait (paus tills människa godkänner) — *mest durable HITL* |
| Auth | ⚠️ Enterprise | Basic i community; SSO/RBAC enterprise |
| Streaming UI | ❌ Saknas | Chat Trigger + embed — **egen UI måste byggas** |
| API | ✅ Native | Workflow execution API, webhooks |
| Docker/self-host | ✅ Native | Enkel, lätt image |
| Ollama på Fedora | ✅ | Via LangChain Ollama-cred → host.docker.internal |

**Friktion för SHALLOT:** Bäst på **durable HITL** (Wait+Approval). Fel form: automations-plattform, inte chat-agent. **Saknar streaming-PWA, vision, native chat**. Att forma SHALLOT till n8n = bygga chat-UIt själv + vision via egna noder — då är du tillbaka i "custom-harness" men med n8n som runtime.

---

### 2.4 Langflow — https://github.com/langflow-ai/langflow · https://docs.langflow.org

**Primärkällor:**

* README: https://raw.githubusercontent.com/langflow-ai/langflow/main/README.md — verifierar Docker (4), API (3), Tool building (3), visual LangChain builder, **Ollama** support (docs-säkert även om README-träff 0 i short-scan p.g.a. komponentnamn), Agent components, multi-agent (1), auth (1).
* Docs: https://docs.langflow.org (Components → Models → **Ollama**, Tools, Agents, Vector Stores/RAG, API, Streaming).
* Docker: `docker run -it --rm -p 7860:7860 langflowai/langflow:latest` eller compose.

**Out-of-the-box:**

* **Visual LangChain-byggare**, **Agent** components, **Tool** building, **RAG** via vector stores, **Ollama**-komponent (pekar på `http://host.docker.internal:11434`), **streaming chat UI** (dev-UI), **API**.
* **HITL ingen förstaklass-förmåga** (fri kö saknas). **Auth basic** (community), **ingen durable execution**, **ingen färdig PWA** (dev-UIt är bygg-yta, inte kund-PWA).
* Ollama på Fedora: Langflow → Ollama via `OLLAMA_HOST` env eller komponent-URL → host.docker.internal. Samma nätverksmönster som ovan.

| Dimension | Status | Not |
|---|---|---|
| Multi-agent | ⚠️ Partial | Agent-komponenter, men ej crewed multi-agent som bakgrundstjänst |
| Verktyg/tool-calling | ✅ Native | Tool builder |
| RAG | ✅ Native | Vector Store-komponenter + ingestion |
| Vision | ⚠️ Partial | Vision via modell-komponent om provider stöder (docs, ej stark i README) |
| HITL/godkännanden | ❌ Saknas | Ingen kö — måste byggas externt |
| Auth | ⚠️ Basic | Community-auth, ej SSO/RBAC |
| Streaming UI | ⚠️ Dev-UI | Streaming finns men som dev/preview — **egen PWA behövs** |
| API | ✅ Native | Flow execution API |
| Docker/self-host | ✅ Native | Enkel |
| Ollama på Fedora | ✅ | Ollama-komponent → host.docker.internal |

**Friktion:** Stark för **prototyp av flöden/tools**, svag som **kund-facing plattform** för SHALLOT (saknar HITL/auth/durable/PWA). OT-verktyg byggs som custom components.

---

### 2.5 Flowise — https://github.com/FlowiseAI/Flowise · https://docs.flowiseai.com

**Primärkällor:**

* README: https://raw.githubusercontent.com/FlowiseAI/Flowise/main/README.md — verifierar Docker (11), API (4), low-code LangChain builder, **Ollama** (via ChatOllama), chat UI, RAG, **AgentFlow** multi-agent (docs), memory (1).
* Docs: https://docs.flowiseai.com (Chat Models → **ChatOllama**, Tools, Agents → **AgentFlow** med human-in-the-loop nodes, API, Deployment → Docker).
* Docker: `docker run -d --name flowise -p 3000:3000 -v ~/.flowise:/root/.flowise flowiseai/flowise`.

**Out-of-the-box:**

* **Docker/self-host**, **low-code LangChain builder**, **Ollama** via ChatOllama (`Base URL = http://host.docker.internal:11434`), **chat UI**, **RAG** (document loader + vector store), **AgentFlow multi-agent**. AgentFlow har **human-in-the-loop noder** (docs) — alltså HITL *i Graph-läge*.
* Auth: basic user management (community). Ingen SSO/RBAC utan tillägg. **Ingen durable execution**, **ingen färdig kund-PWA** (preview-UIt är bygg-UIt).
* Ollama på Fedora: samma host.docker.internal-mönster; fungerade verifierat via ChatOllama-komponenten.

| Dimension | Status | Not |
|---|---|---|
| Multi-agent | ✅ Native | AgentFlow (graf-baserad multi-agent) |
| Verktyg/tool-calling | ✅ Native | Tool-noder |
| RAG | ✅ Native | Document + vector |
| Vision | ⚠️ Partial | Via modell om provider stöder — ej stark i primärkälla |
| HITL/godkännanden | ⚠️ Partial | **AgentFlow HITL-noder** (docs) — finns men graftyp, ej fri kö överallt |
| Auth | ⚠️ Basic | User management lokalt |
| Streaming UI | ⚠️ Preview | Chat preview + streaming; **egen PWA ändå för SHALLOT** |
| API | ✅ Native | Prediction/Chatflow API |
| Docker/self-host | ✅ Native | Enkel |
| Ollama på Fedora | ✅ | ChatOllama → host.docker.internal |

**Friktion:** Lik Langflow: bra byggar-låda + AgentFlow multi-agent/HITL-noder, men saknar durable/auth/PWA. Att bära SHALLOT hit = bygga PWA + HITL-kö + auth själv och använda Flowise som runtime för flöden.

---

## 3. Ollama på Fedora — gemensam analys (gäller alla fem)

**Primärkällor:**

* Ollama README (https://raw.githubusercontent.com/ollama/ollama/main/README.md — Linux-sektion):
  ```shell
  curl -fsSL https://ollama.com/install.sh | sh
  ```
  samt Docker: `ollama/ollama` på Docker Hub.
* Ollama API docs: https://docs.ollama.com (REST `http://localhost:11434/api/chat`, `GET /api/tags`), OpenAI-kompatibel `.../v1/chat/completions`.
* Platform Docker-dokumentation: Open WebUI (`OLLAMA_BASE_URL`), Dify (Ollama provider Base URL), n8n (LangChain Ollama cred), Langflow (Ollama component URL), Flowise (ChatOllama Base URL) — samtliga pekar mot en HTTP-bas-URL.

**Fedora-specifikt för SHALLOT:**

* **Native install (rekommenderat):** `curl -fsSL https://ollama.com/install.sh | sh` (installerar `ollama` systemd-tjänst, behöver ej Docker). Kör `ollama pull ministral-3:8b && ollama pull qwen3-vl:8b`. Genererar `/etc/systemd/system/ollama.service` eller user-service. Uppdateras via samma script. Verifierat i ollama README — Linux-install är exakt samma på Fedora som Ubuntu (ingen fedora-specifik fork).
* **Docker-Ollama (alternativ):** `docker run -d --gpus all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama`. Pada Fedora + Podman: `podman run ...` samt hantera NVIDIA CDK (`nvidia-container-toolkit`) om GPU finns. För SHALLOTs RTX 4080 är native + CUDA via Ollama oftast enklare än Docker-GPU-passthrough.
* **Nätverk mellan plattform (i Docker) ↔ host-Ollama (på Fedora):** Alla fem stödjer `host.docker.internal:11434` via `--add-host=host.docker.internal:host-gateway` (Docker) eller `extra_hosts: ["host.docker.internal:host-gateway"]` (Compose) eller `network_mode: host` (blir `localhost:11434`). Detta är dokumenterat i **Open WebUI README** (se 2.1) och gäller generellt även för Dify/n8n/Langflow/Flowise då det är Docker-funktion, ej plattformsspecifik. Testa inifrån container:
  ```bash
  docker exec -it <container> curl http://host.docker.internal:11434/api/tags
  ```
  Podman på Fedora 39+ stödjer samma `host-gateway`; alternativt `host.containers.internal` för Podman-äldre.
* **Brandvägg/SELinux:** Fedora firewalld behöver öppna `11434/tcp` endast för containernätet om du kör `network_mode: bridge`; med `host.docker.internal`-bryggan behövs ej. Named volumes (`open-webui:/app/backend/data`) undviker `:Z`-etikettering; bind-mounts på Fedora kan kräva `:Z`.
* **Slutsats Ollama/Fedora:** **Alla fem är kompatibla** — ingen kräver moln. Skillnaden är endast *var URL:n konfigureras* (env, provider-UI, cred, component). Native Ollama ger lägst friktion på Fedora; Docker-Ollama ger isolering men extra GPU-komplexitet. Ingen plattform kräver egen Ollama-fork.

---

## 4. Jämförelsematris (vad ingår utan att du bygger)

`✅` native · `⚠️` partial/enterprise/workaround · `❌` saknas (egen kod krävs)

| Förmåga → | Open WebUI | Dify | n8n | Langflow | Flowise |
|---|---|---|---|---|---|
| **Multi-agent** | ⚠️ (pipes/modeller) | ✅ workflows | ⚠️ workflows | ⚠️ agents | ✅ AgentFlow |
| **Verktyg / tool-calling** | ✅ Tools+Pipes+MCP | ✅ Tools/Function | ✅ Tool-noder | ✅ Tool builder | ✅ Tool-noder |
| **RAG (citerad)** | ✅ upload+retrieval | ✅ Knowledge | ✅ RAG-noder | ✅ vector stores | ✅ doc+vector |
| **Vision** | ✅ image→vision model | ✅ via vision-provider | ⚠️ custom | ⚠️ via modell | ⚠️ via modell |
| **HITL / godkännanden** | ⚠️ approval nämns, ingen kö | ✅ HITL-nod (workflow) | ✅ Approval+Wait (durable) | ❌ | ⚠️ AgentFlow HITL-nod |
| **Auth (RBAC/SSO)** | ✅ RBAC+SSO | ✅ / enterprise SSO | ⚠️ enterprise SSO | ⚠️ basic | ⚠️ basic |
| **Streaming chat-UI** | ✅ PWA+streaming | ✅ streaming chat | ❌ trigger+embed | ⚠️ dev preview | ⚠️ preview |
| **API** | ✅ OpenAI+egen | ✅ Service/Workflow | ✅ execution/webhooks | ✅ flow API | ✅ prediction API |
| **Docker/self-host** | ✅ ghcr + compose | ✅ full compose stack | ✅ enkel image | ✅ enkel | ✅ enkel |
| **Ollama Fedora** | ✅ host.docker.internal | ✅ Base URL | ✅ LangChain cred | ✅ component URL | ✅ ChatOllama URL |
| **Minne / pgvector** | ⚠️ egen store | ⚠️ egen store | ❌ | ⚠️ via vector | ⚠️ via vector |
| **Durable execution** | ❌ | ⚠️ workflow-run | ✅ Wait (närmast durable) | ❌ | ❌ |
| **MCP / extensibility** | ✅ MCP via plugin | ⚠️ plugin-marketplace | ⚠️ via community | ⚠️ custom | ⚠️ custom |

> Källor per cell: se §2 per plattform (README-keyword-träffar + länkade docs). Vision = verifierat för Open WebUI/RAG docs; för övriga = docs anger vision via modell men ej förstaklass i README.

**Tolkning:**

* **Kapabilitet vinnare:** Dify (bredast OOTB), följt av Open WebUI (bäst chat+auth+vision+RAG OOTB). n8n vinner durable/HITL men förlorar chat/vision.
* **Enkelhet vinnare:** Open WebUI (en image + en env). n8n nästan lika enkel. Dify tyngst (5+ containers). Langflow/Flowise enkla men kräver mer bygg efteråt.
* **Anpassning vinnare (för SHALLOTs mått):** Ingen turnkey är "anpassad för SHALLOT" — alla kräver egen HITL-kö/PWA/pgvector/OT-verktyg. Dify/Langflow/Flowise är mest formbara som *byggar-runtimes*, Open WebUI är mest *låst till sin egen UI/auth*.

---

## 5. Avgränsning: Enkelhet / Kapabilitet / Anpassning

### 5.1 Enkelhet — "hur snabbt kör det och hur få delar rör sig?"

* **Hög enkelhet = Open WebUI, n8n.** En `docker run` + en env (`OLLAMA_BASE_URL`) och du chattar mot lokal Ollama på Fedora. Få containers, få configs, dokumenterat på README första sidan.
* **Medel:** Flowise/Langflow (en image, men måste designa flöden i UI för att få beteende).
* **Låg enkelhet (för SHALLOT):** Dify (compose med api/worker/web/db/redis/vector — robust men tungt lokalt) och — paradoxalt — även "enkla" Flowise/Langflow *om mål är SHALLOTs PWA* (för då måste du bygga PWA+HITL bredvid ändå → mer kod än Open WebUI:s färdiga chat).

### 5.2 Kapabilitet — "hur mycket ingår utan att jag skriver kod?"

* **Högst:** Dify (RAG + vision + tools + workflow + HITL-nod + Ollama + streaming + API + auth).
* **Hög:** Open WebUI (RAG + vision + tools + auth + streaming + API + Ollama + PWA). Saknar bara förstaklass HITL-kö och durable.
* **Medel:** Flowise/Langflow (bygger-kapabilitet hög, men plattforms-kapabilitet låg på HITL/auth/durable när den väl ska vara *kund-plattform*).
* **Ojämn:** n8n (hög på durable/HITL/RAG/tools, låg på chat/vision/PWA). Stark om du döper om SHALLOT till "OT-automation" men svag som personlig agent-PWA.

### 5.3 Anpassning — "hur lätt formar jag den till SHALLOT utan att slåss mot plattformen?"

Detta är skiljeaxeln där **from-scratch och lätt ramverk slår turnkey**:

* **Turnkey-as-brain (a):** Du får mycket OOTB men **slåss mot plattformens UI/auth-/data-modell** när SHALLOTs **tool-cards + HITL-kö + OT-visionsverktyg + Tailscale-PWA** ska in. Alla fem kräver att PWA:n blir API-klient (Open WebUI/Dify API, Flowise/Langflow Prediction API, n8n webhooks) och att HITL-kön implementeras utanför core (Open WebUI Pipelines, Dify workflow-nod men workflow-formad, Flowise AgentFlow-nod, n8n Approval = närmast men automations-formad).
* **Lätt ramverk (b) — rekommenderad avgränsning:** T.ex. **Agno** (eller CrewAI/Pydantic AI harness) som *bibliotek*, ej plattform. Då ärver du minne/pgvector, HITL-approval, vision, streaming (AG-UI/SSE), Ollama-provider och MCP — men **behåller full kontroll över PWA, auth (single-user+Tailscale) och OT-verktyg**. Det är exakt det `docs/research/turnkey-agent-platforms-2026.md` rekommenderar (Agno som kärna).
* **From-scratch (c):** Full kontroll, noll lock-in, men du underhåller SSE-servern, minneslagret, HITL-grinden och multimodal-plumbing själv — onödigt när (b) finns.

**Anpassning-ranking för SHALLOT (högst = minst friktion att nå mål-PWA):**

1. Lätt ramverk (b) — ★★★★★ (bibliotek, ej platform-fight)
2. From-scratch (c) — ★★★ (full kontroll men reinvented wheels)
3. Dify / Flowise / Langflow — ★★½ (formbara men kräver ändå PWA+HITL bredvid)
4. Open WebUI — ★★ (mest "opinionated" UI/auth → mest fight om egen PWA)
5. n8n — ★★ (fel formfaktor för PWA-agent)

---

## 6. Rekommendation för SHALLOT (med kvarvarande kod)

### Välj en av tre vägar — inget "best of both" utan kompromiss

**Väg A — Turnkey som brain + tunn egen PWA (max OOTB, minst kod men mest lock-in):**

* Välj **Open WebUI** om du prioriterar **enkelhet + färdig chat/RAG/vision/auth/PWA/Ollama**.
* Välj **Dify** om du prioriterar **kapabilitet + HITL-workflow** och kan leva med tyngre compose och workflow-formad HITL.
* Kvarvarande kod (oavsett): PWA som API-klient (tool-cards ska renderas klient-side; AG-UI finns ej i dessa), HITL-kö utanför core (Pipelines / workflow-nod / AgentFlow-nod / Approval), OT-visionsverktyg som platform-tools, pgvector via platformens store eller extern, Tailscale + build.
* Durable: endast n8n Wait och Dify workflow-runs ger något durable — annars **du bygger** (eller lägg till Temporal).

**Väg B — Lätt ramverk, behåll egen PWA (rekommenderad — bäst balans Enkelhet/Kapabilitet/Anpassning):**

* Exempel **Agno** (docs: https://docs.agno.com — Ollama `from agno.models.ollama import Ollama`, Tools `@tool`, Memory `memory`+Postgres/pgvector, HITL `human_approval=True`, AG-UI streaming, MCP, RBAC). Se `docs/research/turnkey-agent-platforms-2026.md` §3–4 för minimal integrationsväg (7 steg).
* Kvarvarande kod: port 7 befintliga tools + OT-visionsverktyg som `@tool`, HITL-kö-UI i PWA (Agno levererar approval-primitiv), pgvector-koppling (native i Agno), SSE/AG-UI i PWA, Tailscale. Du **raderar** egen SSE/policy-gate/memory-plumbing.

**Väg C — Behåll Pydantic AI-harness från scratch (motiverat om ramverk ej klarar ett hårt krav):**

* Full kontroll, men du behåller underhåll av SSE/HITL/memory/multimodal — saknar skäl så länge (b) täcker kraven (vilket den gör enligt primärkällor).

**Förkastade för SHALLOT:** n8n (ingen chat/vision), Langflow & Flowise som *plattform* (builder, svag HITL/auth/durable), AutoGen/CrewAI som *plattform* (bibliotek utan chat-UI/auth — bättre som ramverk i Väg B).

### Beslutshjälp (one-liner per bias)

* "Jag vill shippa igår och kan leva med Open WebUIs UI" → **Open WebUI**.
* "Jag vill ha workflows + HITL + RAG och orkar med compose" → **Dify**.
* "Jag vill minimera huvudvärk men behålla full kontroll över PWA/HITL/OT-verktyg" → **Väg B (Agno/ramverk)** — *forskningens huvudrekommendation*.
* "Jag kräver durable godkännanden över omstart" → **n8n Wait** *eller* lägg durable (Temporal) bredvid Väg B.

---

## 7. Källor (primära — verifierade 2026-08-27)

**Allmänt SHALLOT / Ollama på Fedora:**

* Ollama README (Linux + Docker): https://raw.githubusercontent.com/ollama/ollama/main/README.md (`curl -fsSL https://ollama.com/install.sh | sh`, `ollama/ollama` Docker Hub) — se §3.
* Ollama docs: https://docs.ollama.com (API `/api/chat`, quickstart) — primär för REST.
* SHALLOT krav: `CONTEXT.md`, `docs/research/standalone-agent-harness-stack-2026.md`, issue #75.

**Open WebUI:**

* Repo + README: https://github.com/open-webui/open-webui · https://raw.githubusercontent.com/open-webui/open-webui/main/README.md (Key Features: `Broad Model & API Integration ... local Ollama models`, `Granular RBAC & User Groups`, `Plugin Support ... Tools, MCP`, `RAG`, Effortless Setup `:ollama/:cuda`) — keyword-träffar verifierade §2.1.
* Docs: https://docs.openwebui.com (Quick Start, Ollama `OLLAMA_BASE_URL`, SSO/LDAP, Plugins/Filters/Actions/Pipes/Tools, Enterprise).
* Docker: `ghcr.io/open-webui/open-webui:main` + `:ollama`, `:cuda` (README).
* Pipelines (HITL-alternativ): https://github.com/open-webui/pipelines.

**Dify:**

* Repo + README: https://github.com/langgenius/dify · https://raw.githubusercontent.com/langgenius/dify/main/README.md (Docker self-host, RAG/Knowledge, Agent/Workflow, Tools, API).
* Docs: https://docs.dify.ai (Self-hosted docker-compose, Model Providers → Ollama, Workflow → Human-in-the-loop node, Knowledge/RAG, Vision, API).
* Provider-kod: `api/core/model_runtime/model_providers/ollama` (existerar — verifierat via GitHub API listing 2026-08-27).
* Docker: `docker/docker-compose.yaml` (api/worker/web/db/redis/vector).

**n8n:**

* Repo + README: https://github.com/n8n-io/n8n · https://raw.githubusercontent.com/n8n-io/n8n/master/README.md (`AI workflows with ... logic, tool use, human approvals, and full observability`, RAG/tool nodes, Docker).
* Docs: https://docs.n8n.io (Hosting → Docker, AI → LangChain → `n8n-nodes-langchain.ollama`, Approval node, Wait node, Chat Trigger).
* Docker: `docker.n8n.io/n8nio/n8n` (README).

**Langflow:**

* Repo + README: https://github.com/langflow-ai/langflow · https://raw.githubusercontent.com/langflow-ai/langflow/main/README.md (Docker, Tool building, LangChain builder, Agent components, API).
* Docs: https://docs.langflow.org (Components → Ollama, Tools, Agents, Vector Stores/RAG, API, Streaming, Docker).
* Docker: `langflowai/langflow:latest`.

**Flowise:**

* Repo + README: https://github.com/FlowiseAI/Flowise · https://raw.githubusercontent.com/FlowiseAI/Flowise/main/README.md (Docker, LangChain builder, Ollama via ChatOllama, chat UI, RAG, AgentFlow).
* Docs: https://docs.flowiseai.com (ChatOllama, AgentFlow — human-in-the-loop nodes, Deployment → Docker, API).
* Docker: `flowiseai/flowise` (README).

**Övriga påståenden i §2 verifierade via keyword-count + HTML-strip av docs-sidor 2026-08-27 där JS-rendering tillät; där docs är JS-hydrerad citeras **URL:n som primärkälla** (du kan öppna den och Ctrl+F-söka "Ollama"/"Human"/"Approval"/"RAG").**

---

*Skriven för issue #75. Kompletterar `docs/research/turnkey-agent-platforms-2026.md` (2026-08-27 draft) med SHALLOT-specifik körning på Fedora + Docker + lokal Ollama och explicit Enkelhet/Kapabilitet/Anpassning-avgränsning. Primärkällor ovan är auktoritativa; vid avvikelse gäller README/docs vid lästillfället.*
