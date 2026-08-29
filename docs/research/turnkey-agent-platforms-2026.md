---
title: Turnkey / partially-finished self-hostable agent platforms for SHALLOT
date: 2026-08-27
status: draft
context: |
  SHALLOT = single-user, local-first, privacy-sensitive personal AI agent
  (PM / dev / research / cybersec / OT-hardware). Currently a hand-rolled
  Pydantic AI 0.8.1 harness (agent + 7 tools + policy/HITL gate + stdlib SSE
  server). Question: keep from-scratch, adopt a lightweight framework, or adopt
  a turnkey platform as the "brain" behind a thin custom PWA?
  Harness spec: local Ollama (ministral-3:8b / qwen3-vl:8b), vision, tool use,
  HITL approvals, Next.js+shadcn PWA over Tailscale, streaming chat + tool
  cards + approval UI, pgvector memory, durable execution, ~€20/mo.
method: |
  Claims verified against primary sources only (official GitHub READMEs and
  official docs). Source text was pulled directly from each project's
  repository README / docs site and keyword-matched. Where a capability is
  framework-known but not present in the README snippet fetched, it is marked
  "(docs)" and linked for the user to confirm at current version.
---

# Turnkey / partially-finished self-hostable agent platforms (2026)

## 1. Platform survey (primary-source evidence)

All projects below are self-hostable via Docker unless noted. "Ollama" = runs
against a local Ollama endpoint (OpenAI-compatible or native provider).

### Open WebUI — https://github.com/open-webui/open-webui · https://docs.openwebui.com
Out of the box (from README): **Ollama** (first-class, `OLLAMA_BASE_URL`),
**function/tool calling**, **RAG** (document upload + retrieval w/ citations),
**vision/multimodal** (image upload to vision models), **Artifacts**,
**RBAC**, **SSO/LDAP**, **PWA** (installable), **API** (OpenAI-compatible +
own), **streaming**. README also lists an **approval** capability.
HITL tool-confirmation is limited/partial — there is no first-class
approve-before-tool-execution queue in core; richer middleware needs the
separate "Open WebUI Pipelines" repo. Deploy: `docker` + compose.
- Native: chat UI, auth, RAG, vision, tool calling, PWA, Ollama.
- Not native: durable workflow execution, a structured HITL approval *queue*.

### Dify — https://github.com/langgenius/dify · https://docs.dify.ai
Out of the box (README): **Docker**, **self-host**, **Function Call**, **RAG**,
**API**, **tool** use, visual **Workflow + Agent** builder, multi-agent via
workflows, **Ollama** as a model provider (docs), **vision/multimodal** models
(docs). Dify docs describe a **Human-in-the-loop** approval node in workflows
(docs.dify.ai). Auth: workspace members + SSO (enterprise). Streaming chat UI.
- Native: RAG, tool calling, vision, workflow orchestration, HITL approval
  node, Ollama, auth, streaming UI, API.
- Not native: a *custom* PWA; durable execution beyond workflow runs.

### n8n — https://github.com/n8n-io/n8n · https://docs.n8n.io
Out of the box (README): **Docker**, **self-host**, **AI workflows** with
"logic, tool use, **human approvals**, and full observability", **RAG** nodes,
**tool** nodes. Connects to Ollama via LangChain/OpenAI-compatible creds.
Has an **Approval** node for human-in-the-loop, and a "Wait" node — i.e.
stateful/durable execution (closest to "Temporal-style" of the survey).
No built-in chat UI (Chat Trigger + embed only); multimodal/vision is limited;
auth/SSO is mostly enterprise.
- Native: durable workflow execution, HITL approval node, tool use, RAG, Ollama.
- Not native: chat UI, multimodal vision, a custom PWA.

### Langflow — https://github.com/langflow-ai/langflow · https://docs.langflow.org
Out of the box (README): **Docker**, **API**, **tool** building, visual
LangChain builder, **Ollama** support, Agent components, RAG via vector stores,
streaming chat UI. HITL is not a first-class feature. Auth is basic.
- Native: visual agent/tool builder, RAG, Ollama, streaming, API.
- Not native: HITL queue, durable execution, rich auth, PWA.

### Flowise — https://github.com/FlowiseAI/Flowise · https://docs.flowiseai.com
Out of the box (README): **Docker**, **self-host**, **API**, low-code LangChain
builder, **Ollama**, chat UI, RAG, **AgentFlow** multi-agent. AgentFlow has
human-in-the-loop nodes (docs). Auth: basic user management.
- Native: visual builder, RAG, Ollama, agent/HITL (AgentFlow), API.
- Not native: durable execution, rich auth, custom PWA.

### Agno (formerly Phidata) — https://github.com/agno-agi/agno · https://docs.agno.com
Out of the box (README): **Docker**, **RBAC**, **approval**, **confirm**,
**memory**, **RAG**, **tool** (100+ integrations), **Ollama** provider,
**multimodal/vision** (docs), **reasoning**, and notably
"[Human approval](https://docs.agno.com/runtime/human-approval) — pause runs
for user confirmation; block tools that require admin approval" (verbatim from
README). Runtime exposes a **REST API**, a **Postgres** store for data/traces,
an **MCP server**, and **Interfaces** including **AG-UI** (the streaming UI
protocol) plus Slack/Telegram/Discord/A2A. Agno Platform adds a Playground UI.
- Native: multi-agent, tool calling, memory (incl. Postgres/pgvector), RAG,
  vision, HITL tool approval, Ollama, REST API, AG-UI streaming, RBAC.
- Not native: the custom Next.js PWA shell, Tailscale deploy, OT vision *tools*
  (we write those as Agno tools).

### CrewAI — https://github.com/crewAIInc/crewAI · https://docs.crewai.com
Out of the box (README): **Ollama**, **Tool** (30+ mentions), **memory**,
**RAG**, **human-in-the-loop**, and a linked doc
"[Having Human input on the execution](https://docs.crewai.com/en/learn/human-input-on-execution)".
Role-based agents + tasks + crews/flows. Vision/multimodal in newer versions.
No native chat UI (CrewAI Studio is separate; enterprise platform is paid).
- Native: multi-agent, tool calling, memory, RAG, Ollama, HITL (human input).
- Not native: streaming chat UI, auth, durable execution, custom PWA.

### Microsoft AutoGen — https://github.com/microsoft/autogen · https://microsoft.github.io/autogen/
Out of the box (README): **Tool**/**tool** calling, **RAG**, **stream**ing,
"multi-agent AI applications that can act autonomously or **work alongside
humans**" (verbatim). AutoGen 0.4 = Core + AgentChat + Studio. HITL via
`HumanProxyAgent` / `human_input_mode` (docs). Ollama usable via llm_config.
No self-hosted platform/auth — it is a library (+ AutoGen Studio UI).
- Native: multi-agent, tool calling, streaming, HITL (HumanProxy), Ollama.
- Not native: auth, durable execution, chat UI (Studio is dev-only), PWA.

### PraisonAI — https://github.com/MervinPraison/PraisonAI
Out of the box (README): **Docker**, **self-host**, **Ollama**, **Multimodal**,
**RAG**, **Memory**, **Stream**, **Tool** (many), **Approval**/**vision**,
low-code multi-agent (built on AutoGen/CrewAI). Less mature / smaller community.
- Native: multi-agent, tools, RAG, memory, vision, Ollama, HITL (approval).
- Not native: robust auth, durable execution, mature PWA.

### Agent Zero — https://github.com/frdel/agent-zero
Out of the box (README): **Docker**, **Memory**, **Tool** (self-building agent
that writes/executes its own code), **vision/multimodal** (vision model),
persistent file system, web UI. Designed as a personal, general-purpose agent.
HITL = confirmation before executing shell commands (docs).
- Native: general-purpose agent, tool execution, vision, memory, Ollama, UI.
- Not native: structured approval *queue*, durable execution, custom PWA, auth.

### Also noteworthy (primary sources)
- **LibreChat** — https://github.com/danny-avila/LibreChat : Ollama via litellm,
  tool/plugin calling, RAG (file upload), vision, **SSO/RBAC**, streaming,
  installable web app. Strong chat-UI alternative to Open WebUI.
- **OpenHands** (ex-OpenDevin) — https://github.com/All-Hands-AI/OpenHands :
  coding agent that **asks for confirmation before executing actions** (HITL),
  self-hostable; coding-focused, not a general PM/OT assistant.

## 2. Option analysis for SHALLOT's profile

Profile: single user, local-first, private, Ollama-backed, custom Next.js+shadcn
PWA over Tailscale, streaming chat + tool cards + HITL approval UI, pgvector
memory, durable execution, ~€20/mo.

### (a) Turnkey platform as brain + thin custom PWA
Use e.g. Open WebUI or Dify as the agent/runtime and build the PWA on top of
its API. **Maximizes OOTB**: auth/RBAC/SSO, RAG, vision, tool calling, streaming,
Ollama all handled. **Cost**: you fight the platform's own UI/auth model; the
"custom PWA with tool cards + approval UI" becomes an API client (AG-UI / Dify
API / Open WebUI API). HITL approval *queue* is the friction point — Open WebUI
has only partial approval; Dify has an HITL workflow node but it's workflow-
shaped, not a free-form agent approval queue.

### (b) Lightweight framework instead of raw Pydantic AI
Use **Agno** (or CrewAI) as the agent library; keep the custom PWA + SSE/AG-UI
streaming. Agno natively covers the exact SHALLOT pain points: multi-agent,
tool calling, **memory with Postgres/pgvector**, **RAG**, **vision**,
**HITL human-approval (block admin tools)**, **Ollama**, **REST API + AG-UI
streaming**, RBAC, MCP server. This removes the wheel-reinvention (memory
store, streaming protocol, approval gate, multimodal handling) while keeping
full control of the PWA and tools. Strongest fit for "minimize headaches, keep
control."

### (c) Keep from-scratch Pydantic AI harness
Full control, zero platform lock-in, but you keep maintaining the SSE server,
memory layer, HITL gate, multimodal plumbing, and tool orchestration — the
exact "rebuilding wheels" the user is tired of. Justified only if Agno/CrewAI
cannot meet a hard requirement (they can).

## 3. Custom code that remains per option

| SHALLOT need | (a) Turnkey (Open WebUI/Dify) | (b) Agno framework | (c) Pydantic AI now |
|---|---|---|---|
| Agent + tool orchestration | Platform | Agno (native) | Us (have) |
| Multi-agent | Platform / workflows | Agno (native) | Us |
| Tool calling | Platform | Agno (native) | Us (have) |
| RAG / knowledge | Platform (native) | Agno (native) | Partial/Us |
| Vision/multimodal | Platform (native) | Agno (native) | Us (have) |
| Memory (pgvector) | Platform (its own store) | Agno memory→pgvector (native) | Us |
| HITL approval *queue* + UI | Partial (Open WebUI weak; Dify workflow node) → **Us build queue/UI** | Agno blocks admin tools (native); **Us build queue + approval UI** | Us (have) |
| Streaming chat + tool cards | Platform UI / API | Agno + AG-UI (native streaming) → **Us render in PWA** | Us (have, slow) |
| Custom Next.js+shadcn PWA | **Us (thin API client)** | **Us (AG-UI client)** | Us (have) |
| Tailscale / PWA packaging | **Us** | **Us** | Us (have) |
| OT hardware vision tools | **Us (as platform tools)** | **Us (as Agno tools)** | Us (have) |
| Durable execution (Temporal-style) | Dify/n8n workflows; else **Us** | Agno runs (not durable orchestration) → **Us / add Temporal** | Us |

Net: in (b), the only genuinely *new* code vs today is swapping the harness core
for Agno and re-hosting the 7 tools + OT vision tools as Agno tools; HITL queue
UI, PWA, Tailscale, pgvector wiring are still ours but Agno supplies the
approval primitive and memory backend. In (a), you trade PWA control for more
OOTB but still build the approval queue/UI and the API-client PWA.

## 4. Recommendation

**Adopt option (b): Agno as the agent/runtime core, keep the custom Next.js PWA
as the front-end over Agno's AG-UI streaming protocol.** Rationale (primary
sources):
- Agno natively delivers the four things we are rebuilding: **memory** (Postgres
  store, pgvector), **HITL human approval** (docs.agno.com/runtime/human-approval
  — "block tools that require admin approval"), **multimodal/vision**, and
  **AG-UI streaming** + REST API + MCP server (agno README).
- It is a library, not a platform: no fight over UI/auth, full control of the
  PWA, Tailscale, and OT tools. Local Ollama is a first-class provider.
- Lighter than from-scratch Pydantic AI: we delete the SseServer/policy-gate/
  memory-plumbing we wrote and reuse Agno's.

**Minimal integration path (primary docs):**
1. Install: `pip install agno` — https://docs.agno.com/introduction
2. Ollama model: `from agno.models.ollama import Ollama; Ollama(id="ministral-3:8b")` — https://docs.agno.com/models/ollama
3. Agent + tools: define `Agent(tools=[...])`; port the 7 existing tools + OT
   vision tools as Agno `@tool` functions — https://docs.agno.com/tools
4. Memory + pgvector: enable `Agent(memory=..., embedder=...)` with Postgres
   backend — https://docs.agno.com/agents/memory
5. HITL: mark sensitive tools `human_approval=True` (blocks until confirmed) —
   https://docs.agno.com/runtime/human-approval
6. Streaming to PWA: expose via **AG-UI** interface (docs.agno.com/runtime/interfaces)
   and render tool calls/cards in the Next.js client.
7. Deploy: Docker on the Fedora node behind Tailscale; Agno supplies Postgres +
   MCP server.

**If the user prefers maximum OOTB and is willing to concede a fully custom
PWA**, choose **Open WebUI** (best OOTB chat+auth+RAG+vision+PWA+Ollama;
API at docs.openwebui.com) or **Dify** (best if workflow/HITL orchestration
matters; docs.dify.ai). Caveat: neither gives a first-class free-form HITL
*approval queue* — that stays custom either way.

**Rejected for SHALLOT:** n8n (no chat UI / vision, automation-shaped), Langflow
& Flowise (builder libraries, weak auth/HITL/durable), AutoGen & CrewAI (great
libraries but no streaming chat UI / auth / durable execution out of the box),
Agent Zero (opinionated general agent, not a controllable runtime for a custom
PWA), PraisonAI (immature).

## Sources (primary)
- Open WebUI: https://github.com/open-webui/open-webui · https://docs.openwebui.com
- Dify: https://github.com/langgenius/dify · https://docs.dify.ai
- n8n: https://github.com/n8n-io/n8n · https://docs.n8n.io
- Langflow: https://github.com/langflow-ai/langflow · https://docs.langflow.org
- Flowise: https://github.com/FlowiseAI/Flowise · https://docs.flowiseai.com
- Agno: https://github.com/agno-agi/agno · https://docs.agno.com
  (human-approval: https://docs.agno.com/runtime/human-approval ;
   interfaces/AG-UI: https://docs.agno.com/runtime/interfaces)
- CrewAI: https://github.com/crewAIInc/crewAI · https://docs.crewai.com
  (human input: https://docs.crewai.com/en/learn/human-input-on-execution)
- AutoGen: https://github.com/microsoft/autogen · https://microsoft.github.io/autogen/
- PraisonAI: https://github.com/MervinPraison/PraisonAI
- Agent Zero: https://github.com/frdel/agent-zero
- LibreChat: https://github.com/danny-avila/LibreChat
- OpenHands: https://github.com/All-Hands-AI/OpenHands

> Verification note: capability keywords were matched directly against each
> project's primary README/docs on the dates above. Version-specific behavior
> (especially HITL queue depth, pgvector wiring, AG-UI client libs) should be
> re-confirmed against the linked docs before implementation.
