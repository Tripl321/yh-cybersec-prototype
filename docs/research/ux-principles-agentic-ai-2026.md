# UX Principles for Agentic AI Dashboards — SHALLOT Harness

**Research date:** 2026-08-27
**Scope:** UX principles for autonomous agents that plan, use tools, ask for approval, and handle human-in-the-loop (HITL); UI patterns for agency, progress, tool calls, approvals, and provenance; autonomy vs control; PWA desktop+mobile; concrete recommendations for SHALLOT's unified dashboard (Pydantic AI + PostgreSQL+pgvector + Temporal, Fedora RTX 4080 16 GB control node, Next.js 16 PWA `shallot-setup` via Tailscale, Chat via mixtral, Vision via llava:13b → mixtral with optional NIM/OpenRouter).
**Method:** Primary sources only — official docs, source repos, specs, first-party APIs, design systems, peer-reviewed/HCI papers. Every claim traced to its owner. Web searches and fetches 2026-08-27.
**Status:** Completed

## Claim labels

- **Verified** — stated by a cited first-party source.
- **Assessment** — engineering judgment derived from verified facts.
- **Open** — not established by reviewed primary material.

---

## Summary

Agentic UX converges on one invariant across Anthropic, OpenAI, Google, Microsoft, and Pydantic AI: **policy lives in versioned code/configuration, not in prompts; the agent proposes, a typed gate pauses execution, and the UI surfaces what/why/with-what-params before a human commits**. Streaming is for observation and early interruption; approval is a persisted, typed interrupt that survives restarts. Provenance and time-travel are first-class (checkpoint + store). PWA installability and responsive dashboard blocks are the cheapest path to a native-feeling unified dashboard. For SHALLOT: keep Next.js 16 + shadcn/ui blocks, add Vercel AI SDK UI's tool-state machine (`approval-requested` → `approval-responded` → `output-available/denied`), Pydantic AI deferred tools, and LangGraph-style checkpoint timeline — and make HITL decisions auditable in Postgres.

---

## 1. Established UX principles for Agentic AI

### 1.1 The ladder: from assisted to autonomous must be earned, not declared

The peer-reviewed Three-Pillar Model (Transparency, Accountability, Trustworthiness) frames autonomy as progressive validation — analogous to autonomous-driving levels — where trust is earned through transparency and accountability at each stage, not assumed by design [Cheng et al., arXiv:2601.06223](https://arxiv.org/abs/2601.06223). The same paper synthesizes HITL, RLHF, and collaborative-AI prior work into staged governance. This directly motivates SHALLOT's separation of the personal harness from the OT Cub agent (ADR-0010 trust boundary): broad autonomy in a personal harness is acceptable, embodied OT actuation is not.

Anthropic's *Building effective agents* makes the engineering corollary explicit: **"augment, don't replace"** — start with the simplest composable pattern (prompt → augmented LLM → workflow → agent) and only escalate to full agent loops when the task genuinely requires autonomous planning and tool use [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents). The companion *Effective harnesses for long-running agents* prescribes a harness that gives the agent tools, tight feedback loops, and human checkpoints [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). Both are **Verified**.

**Principle → implication:** Design for *levels*, not a binary. SHALLOT needs a single harness that can run in four modes per action class (see §3).

### 1.2 Agency is tool use plus loop, not chat

All five frameworks define an agent as a loop that plans, calls tools, and retains state across multi-step work:

- **Anthropic Agent SDK** — the same harness that powers Claude Code, now as `@anthropic-ai/claude-agent-sdk` (Python + TypeScript), with a bundled binary and a tool loop you configure via permissions rather than re-implement [Anthropic — Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) [NPM — @anthropic-ai/claude-agent-sdk](https://www.npmjs.com/package/%40anthropic-ai%2Fclaude-agent-sdk).
- **OpenAI Agents SDK** — distinguishes Responses API (direct model calls) from Agents SDK (SDK owns orchestration, tool execution, approvals, and resumable state via `RunState`/`interruptions`) [OpenAI — Agents SDK](https://developers.openai.com/api/docs/guides/agents) [OpenAI — Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop).
- **Google ADK** — model-agnostic, tool-centric agents with `Confirmation` and `LongRunningFunctionTool` for HITL [Google ADK — Tools documentation](https://google.github.io/adk-docs/tools/) [Google ADK — Human input workflows 2.0](https://google.github.io/adk-docs/workflows/human-input/).
- **Microsoft Agent Framework** — orchestrations + workflows; both use typed approval (`tool.ApprovalRequiredFunc` / `ApprovalRequiredAIFunction`) and `RequestPort`/`RequestInfoEvent` that pause and resume [Microsoft — Function tools with human-in-the-loop approvals](https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval) [Microsoft — Workflows HITL](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) [Microsoft — HITL with AG-UI](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop).
- **Pydantic AI** — one agent definition runs as CLI, web chat, realtime speech, or ACP editor agent; durable execution on Temporal/DBOS with `requires_approval` and `DeferredToolRequests`/`DeferredToolResults` [Pydantic AI — Overview](https://ai.pydantic.dev/) [Pydantic AI — Deferred Tools: Human-in-the-Loop Tool Approval](https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/) [Pydantic AI — Durable execution](https://ai.pydantic.dev/durable_execution/overview).

**Principle → implication:** The dashboard must expose the *loop* (steps, tool calls, interrupts), not just the final answer.

### 1.3 HITL is an architectural contract, not a prompt instruction

Primary sources agree on three invariant rules:

1. **Declare the gate in code.** `requires_approval=True`, `needs_approval`, `requires_approval`, `approval_mode="always_require"`, `toolApproval: {name: 'user-approval'}`, `interrupt_on` — not "please ask before deleting". Pydantic AI explicitly warns approval is *not* an authorization boundary against an untrusted client and must be paired with server-side authz in the tool itself [Pydantic AI — Deferred Tools](https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/). Microsoft wraps tools with `ApprovalRequiredFunc` [Microsoft — Tool approval](https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval). OpenAI requires `needs_approval=True` or an async predicate on the tool definition [OpenAI — Human-in-the-loop (JS)](https://openai.github.io/openai-agents-js/guides/human-in-the-loop).
2. **Pause with persisting state.** OpenAI serializes via `RunState.toString()/fromString()` and resumes with `Runner.run(agent, state)` [OpenAI — Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop). LangGraph checkpoints after every node and restores from `checkpoint_id` [LangGraph — Use time-travel](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel) [LangGraph — Time travel (frontend)](https://docs.langchain.com/oss/python/langchain/frontend/time-travel). Microsoft persists pending `RequestInfoEvent`s inside checkpoints [Microsoft — Workflows HITL](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop). Pydantic AI persists via Temporal/DBOS with `DeferredToolRequests` [Pydantic AI — Deferred Tools](https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/).
3. **Timeout is policy, not model mood.** Anthropic's `canUseTool`/`PreToolUse` has a ~60 s hard limit; long approvals need an external queue + `PermissionRequest` hook [Anthropic — canUseTool/PreToolUse](https://code.claude.com/docs/en/agent-sdk/permissions) [Anthropic — Hooks](https://code.claude.com/docs/en/agent-sdk/hooks) [Claude Agent SDK Python #304/#96 HITL timeout](https://github.com/anthropics/claude-agent-sdk-python/issues/304). OpenAI long-running approvals recommend versioned branching (parallel SDK installs via alias) [OpenAI — Human-in-the-loop: Versioning pending tasks](https://openai.github.io/openai-agents-js/guides/human-in-the-loop). **Assessment:** SHALLOT on Temporal avoids the 60 s trap.

### 1.4 Transparency calibrates trust, and miscalibrated trust is the failure mode

HCI literature is consistent: transparency without calibration produces over-reliance *or* under-reliance. The Three-Pillar Model identifies hallucinations, data bias, and *goal misalignment (inversion problem)* as primary risks requiring transparency + accountability [arXiv:2601.06223](https://arxiv.org/abs/2601.06223). A systematic literature review finds trust in AI-enabled systems depends on *appropriate* transparency, not maximal disclosure [arXiv:2304.08795 — A Systematic Literature Review of User Trust in AI-Enabled Systems: An HCI Perspective](https://arxiv.org/abs/2304.08795). Dissertation work on *Establishing Appropriate Trust in AI through Transparency and Explainability* shows static explanations often increase over-reliance; reliance-aware, interactive explanations perform better [ACM DOI 10.1145/3613905.3638184](https://dl.acm.org/doi/10.1145/3613905.3638184). A 2026 multi-agent transparency study finds early adopters face a "catch-22" between exposing complexity and overwhelming users [arXiv:2606.08323 — How Early Adopters Conceptualize Transparency](https://arxiv.org/abs/2606.08323).

**Principle → implication:** Progressive disclosure. Show agent *intent* and *provenance* by default; hide full reasoning/tool traces behind affordances; require explicit approval for high-stakes *actions* only.

---

## 2. UI patterns for agency, progress, tool calls, HITL, and provenance

### 2.1 The canonical tool-state machine (use it verbatim)

Vercel AI SDK 5 defines the states SHALLOT should render. For tools **with approval**:

`input-streaming` → `input-available` → `approval-requested` → `approval-responded` → `output-available | output-denied` (plus `output-error`) [Vercel AI SDK — Chatbot Tool Usage](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage) [Vercel — Tool Approval detail](https://chatbot.ai-sdk.dev/docs/customization/tool-approval.md).

Without approval the path collapses to `input-streaming` → `input-available` → `output-available`. Every framework echoes this:

- OpenAI: pending `interruptions` array of `RunToolApprovalItem` with `approve()`/`reject()` and `alwaysApprove` [OpenAI — Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop).
- Pydantic AI: `DeferredToolRequests` → `DeferredToolResults` with `ToolApproved`/`ToolDenied` [Pydantic AI — Deferred Tools](https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/) [Pydantic DeepAgents — Human-in-the-Loop Example](https://vstorm-co.github.io/pydantic-deepagents/examples/human-in-the-loop/).
- Microsoft: `TOOL_CALL` → `RUN_FINISHED/interrupt` with `responseSchema: {accepted: bool, arguments: object}`; batched approvals stream sibling `never_require` results in the resumed run [Microsoft — HITL with AG-UI](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop).
- Anthropic: `PreToolUse` (deny/auto-approve) → `canUseTool` (human allow/deny) → `PostToolUse` (audit log) [Anthropic — Hooks](https://code.claude.com/docs/en/agent-sdk/hooks) [Anthropic — Configure permissions](https://platform.claude.com/docs/en/agent-sdk/permissions).
- LangGraph: `interrupt()` → `Command(resume=...)` with persistent `ThreadState` [LangGraph — Human-in-the-loop concepts](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop).

**Verified pattern:** Render each tool as a card with exhaustive `part.state` handling. Vercel's reference UI switches on `part.state` and distinguishes manual vs automatic approvals via `part.approval.isAutomatic` and `part.approval.reason` [Vercel AI SDK — Tool Execution Approval](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage). For SHALLOT's `ai-python.dev` (Vercel AI SDK for Python, beta) the transport is identical: `streamText` → `createUIMessageStreamResponse` → `toUIMessageStream` → `useChat`/`DefaultChatTransport` [Vercel AI SDK — useChat](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat).

### 2.2 Streaming: local-first protocol, not ad-hoc SSE

Vercel's architecture is the closest to SHALLOT's Current UI (Next.js API routes streaming):

- Server: `streamText({model, messages, tools, toolApproval, experimental_toolApprovalSecret})` → `toUIMessageStream({stream: result.stream})` → `createUIMessageStreamResponse` [Vercel — Chatbot Tool Usage](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).
- Client: `useChat({transport: new DefaultChatTransport({api: '/api/chat'}), sendAutomaticallyWhen: lastAssistantMessageIsCompleteWithToolCalls | lastAssistantMessageIsCompleteWithApprovalResponses})` + `onToolCall` for client-side tools + `addToolOutput`/`addToolApprovalResponse` for HITL [Vercel — useChat](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat) [Vercel — Generative UI](https://ai-sdk.dev/docs/ai-sdk-ui) (tool call streaming via `parts`).
- Enable `toolCallStreaming` to stream partial inputs while the model generates them — render as `input-streaming` skeleton [Vercel — Chatbot Tool Usage](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).
- For sensitive tools, set `experimental_toolApprovalSecret` so the server cryptographically verifies it issued the approval [Vercel — Securing Approvals](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).

Terminator for every issue: `result.toDataStreamResponse()` / `toUIMessageStreamResponse()` handles encoding, not hand-rolled `EventSource` [Vercel — useChat](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat).

**Assessment for SHALLOT:** Keep Next.js API routes; migrate from manual streaming to `ai` package's transport. Works with Python backend via `ai-python.dev` because the wire protocol is framework-agnostic (UIMessage stream). The Next.js PWA remains the single rendering layer regardless of whether the agent runs in Python (Pydantic AI) or Node.

### 2.3 Generative UI and AI Elements: progressive disclosure without overwhelm

Vercel distinguishes three layers [Vercel — AI SDK UI overview](https://sdk.vercel.ai/docs/ai-sdk-ui):

- **AI SDK Core** — `generateText`/`streamText` on the server.
- **AI SDK UI** — hooks (`useChat`) that manage chat state and streaming.
- **AI SDK RSC / Generative UI** — stream *components*, not just JSON (`streamUI` / `useActions`) — server chooses the component for a tool result and the client renders it.

Paired with **AI Elements** (the shadcn-based component library for AI: `Conversation`, `Message`, `Reasoning`, `Tool`, `Sources`, `Loader`) [Vercel — AI Elements](https://ai-sdk.dev/docs/ai-elements), the canonical pattern is:

- Always render user/assistant `Message` with `parts`.
- Render agent thinking in a collapsible `Reasoning` block (hidden by default, expandable).
- Render each tool as `Tool` with header `toolName + state badge` + collapsible input/output. For `approval-requested`, promote the card to a modal-like banner with Approve/Deny (see §2.1).
- Stream chart/table/data components generatively rather than serializing raw JSON to the chat gutter.

This matches Anthropic's Cook workflow UI principle: tools and memory are *surfaces*, not logs.

### 2.4 Time-travel and provenance (the missing "audit" surface)

LangGraph's time-travel UI is the strongest primary pattern for provenance:

- Persist after every node: `ThreadState {checkpoint, values, tasks, next}` [LangGraph — Time travel (frontend)](https://docs.langchain.com/oss/python/langchain/frontend/time-travel).
- Fetch history via `get_state_history()` (or LangGraph Platform's thread/history API), render a linear timeline where each checkpoint is an entry; interrupts get amber highlight [LangGraph — Time travel frontend](https://docs.langchain.com/oss/python/langchain/frontend/time-travel) [LangGraph — Use time-travel (Python)](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel).
- Resume with `stream.submit({}, {forkFrom: {checkpointId}})`, which rolls back state then re-executes; for HITL, `Command(resume=...)` replays the interrupt node [LangGraph — Time travel: Resuming](https://docs.langchain.com/oss/python/langchain/frontend/time-travel).
- For production, use a JSON tree viewer (`react-json-view`) and diff state between checkpoints [LangGraph — Frontend time-travel tips](https://docs.langchain.com/oss/python/langchain/frontend/time-travel).

Pydantic AI mirrors this through AG-UI + durability: every agent can emit `UI event streams` (AG-UI, Vercel AI) and survives restarts; the UI event stream is the provenance feed [Pydantic AI — Overview (durability + UI streams)](https://ai.pydantic.dev/) . Microsoft's `Checkpoints and Requests` note that pending requests are saved with checkpoint state and re-emitted on restore [Microsoft — Workflows HITL: Checkpoints and Requests](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop).

**Pattern to copy:** A collapsible "Execution timeline" next to the chat. Minimum: checkpoint dots → expand to `values` + task list. Ideal: diff view between checkpoints.

### 2.5 AG-UI as shared transport for multi-agent + HITL

AG-UI (`@ag-ui/client` / `agent_framework_ag_ui.AGUIChatClient`) standardizes tool events, reasoning, and approval interrupts across frameworks. Microsoft's backend uses `ApprovalRequiredAIFunction` → AG-UI serializes as `RUN_FINISHED/outcome: interrupt` with `responseSchema`; the client resumes with `{threadId, resume: [{interruptId, status: "resolved", payload: {accepted: true}}]}` [Microsoft — HITL with AG-UI](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop). Pydantic AI's AG-UI integration uses the same shape (see `examples/ag_ui/api/human_in_the_loop.py`) [Pydantic AI — AG-UI examples](https://ai.pydantic.dev/examples/ag-ui) [Pydantic AI — AG-UI docs](https://pydantic.dev/docs/ai/overview).

**Assessment:** Adopt AG-UI's interrupt envelope even when not using AG-UI directly; it maps 1:1 to Vercel's `approval-*` states and Pydantic's `DeferredTool*`. This keeps SHALLOT free to use Pydantic AI on the backend and Next.js on the frontend without a custom glue layer.

---

## 3. Dashboard balance: autonomy vs control

### 3.1 When to stream vs summarize

| Signal | Stream (token-by-token + tool states) | Summarize (collapsed / batched) |
|--------|----------------------------------------|--------------------------------|
| User is watching, task <30 s | Yes — gives early abort + calibration | — |
| Multi-step plan (>3 tools) | Stream steps, collapse reasoning | Summarize batch to notification (see below) |
| Background job (hardware test, LoRa scan, research crawl) | Stream to timeline only | Push *outcome card* to Overview + inbox |
| Sensitive/compliance action pending | Stream approval card immediately | Never auto-summarize away the decision |

Vercel's `maxSteps` / `stopWhen: stepCountIs(n)` explicitly caps autonomous chaining [Vercel — Chatbot Tool Usage](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage). LangGraph's `checkpoint` + `interruptBefore/After` is the server equivalent [LangGraph — Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop). **Rule:** Cap autonomous chaining in configuration; surface the cap in UI ("Agent will pause after 5 tool calls for review").

### 3.2 When to require approval

Primary sources converge on an **action manifest** classified by *severity × reversibility*, not per-model confidence alone. Group HITL demand by HITL intensity:

- **Always require** — destructive (delete, overwrite, RF transmit, flashing firmware), external side-effects (send email, pay, publish), compliance gates [Pydantic AI — When to Use HITL](https://vstorm-co.github.io/pydantic-deepagents/examples/human-in-the-loop/) [Microsoft — Function tools: Always require](https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval) [Google ADK — Tool confirmation](https://google.github.io/adk-docs/tools/confirmation/).
- **Conditional** — depends on args/context: `amount > threshold`, `path not in /workspace`, `recipient outside allowlist` [Vercel — Tool Execution Approval: dynamic approval](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage) [Pydantic AI — raise ApprovalRequired from args_validator/context](https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/).
- **Never** (or auto-approve) — read-only, `Read`/`Glob`/`Grep`/vector search [Anthropic — PreToolUse auto-approves read-only](https://code.claude.com/docs/en/agent-sdk/hooks).
- **Human-on-the-loop** — let agent proceed, human can interrupt/rollback within a window; needs durable checkpoint + undo (LangGraph time-travel) [LangGraph — Human-in-the-loop patterns](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop).

**Anti-patterns to avoid** (production HITL study): binary Approve/Deny with no context; forcing reviewers to re-derive the decision; frequent false-positive interrupts causing fatigue and rubber-stamping (corroborated by primary approval UX requiring what/why/params — see Vercel, Microsoft, Pydantic entries below).

**Approval card must contain** (synthesis of Vercel's `part.input` + Microsoft's `FunctionCallContent` + Pydantic's `metadata`):

1. What action + exact params (monospaced, copyable)
2. Why the agent chose it (link to reasoning step)
3. Workflow history (what already happened)
4. Expected outcome + reversibility
5. Risk level + policy reference
6. Approve / Deny (+ reason) / Edit params (if supported). For Vercel, `addToolApprovalResponse({id, approved})` [Vercel — Tool Execution Approval](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage); for AG-UI, `{accepted: bool, arguments?}` [Microsoft — AG-UI HITL](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop).

**Timing and escalation:** Treat thresholds as governance — versioned config, reviewed like code, not live dashboard knobs (governance — see Microsoft and Anthropic: versioned permissions). For SHALLOT, store thresholds in Temporal schedules + Postgres config table, audited. Escalate: if no decision within timeout, emit reminder notification (PWA Badging) and keep run durable, not abort [Pydantic — Best Practices: handle timeouts](https://vstorm-co.github.io/pydantic-deepagents/examples/human-in-the-loop/).

### 3.3 How to show memory and provenance

- **Checkpointer vs store** (LangGraph): checkpointer = thread-scoped short-term memory (conversation continuity, HITL, time travel, fault tolerance); store = cross-thread long-term memory (user preferences, facts, hardware inventory, build logs) [LangGraph — Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence). Map to SHALLOT: Temporal + Postgres checkpointer for threads, pgvector store for project/research memory.
- **Durable tool calls** survive restarts; the approval decision is replayed from history [Pydantic DeepAgents — HITL](https://vstorm-co.github.io/pydantic-deepagents/examples/human-in-the-loop/) [LangGraph — Durable execution](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop).
- **Audit trail**: Anthropic's `PostToolUse` JSONL audit log (tool, input, ts) is the primary provenance pattern for compliance [Anthropic — Hooks](https://code.claude.com/docs/en/agent-sdk/hooks) [Anthropic — Permissions](https://platform.claude.com/docs/en/agent-sdk/permissions). Bridge to Postgres: log every `approval-requested/approval-responded/output-denied` event durably.
- **Citations/sources:** For research and hardware tasks, stream `Sources` parts alongside answers (Vercel AI Elements) and link to vector chunks.

---

## 4. PWA dashboard that feels native on desktop and mobile

### 4.1 What "installable" actually requires

Per web.dev and MDN (primary PWA specs):

- A **Web App Manifest** with `name`, `short_name`, `icons`, `display: standalone`, `start_url`, `theme_color`/`background_color` makes the app installable; desktop browsers surface an install badge; iOS requires manual Add to Home Screen via share menu and `apple-touch-icon` [MDN — Progressive Web Apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps) [web.dev — Installation](https://web.dev/learn/pwa/installation) [W3C — Web App Manifest](https://www.w3.org/TR/appmanifest/).
- **Responsive to any screen size** — "all content available at any viewport size" — is a PWA checklist requirement, not a nice-to-have [web.dev — What makes a good PWA: PWA checklist](https://web.dev/articles/pwa-checklist).
- **Custom offline page** — keep users in the PWA rather than the browser's offline dinosaur; precache the app shell on `install` [web.dev — PWA checklist](https://web.dev/articles/pwa-checklist) [web.dev — Progressive Web Apps](https://web.dev/explore/progressive-web-apps).
- **Service worker caching**: choose per resource — `Cache First` for app shell/static assets, `Network First` for feeds/message history, `Stale-while-revalidate` for docs/models lists [web.dev — Offline UX design guidelines](https://web.dev/articles/offline-ux-design-guidelines) and [web.dev — Service worker caching](https://web.dev/articles/service-worker-caching-and-http-caching).
- **Capabilities unlocked after install**: Badging API, App Shortcuts, Window Controls Overlay (desktop), share target — use Badging to surface `needs-attention` approval counts [MDN — Badging API](https://developer.mozilla.org/en-US/docs/Web/API/Badging_API) [MDN — Window Controls Overlay](https://developer.mozilla.org/en-US/docs/Web/API/Window_Controls_Overlay_API).

**Implication for SHALLOT via Tailscale:** Since there is no app-store distribution, the PWA manifest + install badge *is* the distribution channel; the Tailscale URL must serve manifest + 192/512 icons and not redirect the start_url (PWA requirement).

### 4.2 Responsive dashboard blocks (shadcn/ui + Nuxt UI)

#### shadcn/ui blocks — the current SHALLOT choice

- **Blocks** are pre-built, production-ready sections composed of multiple shadcn/ui components; copy-paste, not NPM lock-in, full ownership [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks) [ui.shadcn.com — Blocks docs](https://ui.shadcn.com/docs/blocks).
- **Dashboard blocks**: `dashboard-01` (sidebar + SectionCards + ChartAreaInteractive + DataTable), sidebar variants (`sidebar-07` collapses to icons), navigation blocks — exactly SHALLOT's current shell [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks).
- **Shell elements:** `SidebarProvider` + `AppSidebar` (variant `inset`) + `SidebarInset` + `SiteHeader` + `@container/main` with `flex flex-col gap-4 py-4 md:gap-6 md:py-6` [ui.shadcn.com — dashboard-01 page.tsx](https://ui.shadcn.com/blocks) pattern.
- **Customization:** blocks are shadcn + Tailwind — modify via props and Tailwind, not via upstream release [Shadcn Dashboard docs](https://shadcndashboard.dev/docs/getting-started/blocks).

#### Nuxt UI Dashboard — the user's second candidate

Nuxt UI (Vue) offers the same shape for Nuxt users: `UDashboardGroup` + `UDashboardPanel` (+ `UDashboardNavbar`/`UDashboardSidebarCollapse`) with `resizable`, `min-size`/`max-size`/`default-size`, stored via `storage` + `storage-key`, plus a free Dashboard template (collapsible sidebar, keyboard shortcuts, light/dark, command palette) [Nuxt UI — DashboardPanel](https://ui.nuxt.com/docs/components/dashboard-panel) [Nuxt UI — Dashboard template](https://dashboard-template.nuxt.dev/) [GitHub — nuxt-ui-templates/dashboard](https://github.com/nuxt-ui-templates/dashboard).

**Assessment:** For SHALLOT (Next.js 16, already on shadcn), Nuxt UI's value is *pattern inspiration*, not a migration target. The `DashboardGroup`/`DashboardPanel` pattern maps 1:1 to shadcn's `ResizablePanelGroup`/`ResizablePanel`. Staying on shadcn preserves ownership and keeps Vercel AI SDK AI Elements (React) native.

#### Mobile-vs-desktop affordances

- **Mobile-first**: per PWA guide, start from key features on small screens, then progressive enhancement [web.dev — PWA checklist](https://web.dev/articles/pwa-checklist).
- **Intrinsic layout**: use CSS Grid for shell (header/sidebar/main) + Flexbox within panels; relative units (`rem`, `vw`, `ch` with `max-inline-size: 66ch`) and `@container` queries (intrinsic design — see web.dev responsive guides).
- **Collapsed sidebar**: `sidebar-07` variant (icons-only) on desktop; on mobile, `Sheet` drawer triggered by hamburger, or bottom tab bar for top-4 routes. Nuxt's `DashboardSidebarCollapse` shows the leading-slot pattern [Nuxt UI — DashboardPanel](https://ui.nuxt.com/docs/components/dashboard-panel).
- **Resizability**: enable only `lg:` (`className="hidden lg:flex"` for secondary panel) per `dashboard-01` — avoids accidental resize on touch [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks).

### 4.3 Adaptive loading and offline for a hardware-adjacent agent

SHALLOT's dashboard must remain useful when the RTX 4080 node or LoRa link is degraded. Primary caching guidance:

- Shell = `Cache First`; user-specific routes (chat history, approvals) = `Network First` with cache fallback; docs/models = `Stale-while-revalidate` [web.dev — PWA checklist](https://web.dev/articles/pwa-checklist).
- Use `Background Sync` for deferred form submissions (e.g., approve while offline, sync on reconnect) [MDN — Offline and background operation](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation).

---

## 5. Concrete recommendations for SHALLOT's unified dashboard

### 5.1 Keep the block foundation, upgrade the stream and the interrupt surfaces

**Do not migrate to Nuxt.** Stay on Next.js 16 + shadcn/ui blocks (already installed: `components.json`, Tailwind v4). Nuxt's Dashboard template is the reference for *layout behavior*, not a dependency change. For `ai-python.dev` curiosity (Vercel AI SDK for Python), the wire protocol already suits SHALLOT: the Python agent can emit the same `UIMessage` stream the Next.js frontend consumes, so the dashboard stays React while the agent stays Python.

**Blocks to keep and add:**

| SHALLOT route | Block / component | Purpose |
|---------------|-------------------|---------|
| Overall shell | `dashboard-01` shell + `sidebar-07` collapsible sidebar | `SidebarProvider` / `AppSidebar variant="inset"` / `SidebarInset` / `SiteHeader` — gives resizable left nav, header with search + notifications, `@container/main` canvas [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks) |
| Overview | `section-cards.tsx` + `chart-area-interactive.tsx` + `data-table.tsx` | KPIs (approvals pending, Temporal queue depth, GPU VRAM, LoRa RSSI), recent runs timeline, needs-attention inbox [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks) |
| Chat | AI Elements `Conversation` + `Message` + `Tool` + `Reasoning` + `Sources` | Streamed chat with tool-state cards; reasoning collapsed by default [ai-sdk.dev — AI Elements](https://ai-sdk.dev/docs/ai-elements) |
| Vision (general, not just breadboard) | `DataTable` lineage + `Tool` card + media preview | Upload/camera → llava:13b → mixtral; show `input-streaming` for caption, then verdict; provenance chips (model, prompt hash) |
| Hardware / Infrastructure | `chart-area-interactive` + status `Badge` + `Alert` banners | Field Node / Mama Bear / SX1262 / RP2350 telemetry; use same pattern as `section-cards` |
| Security / Models / Settings | Form blocks + tables | Model selector (RTX 4080 fit), secrets (SOPS), Tailscale/PWA settings |

### 5.2 Navigation: group by intent, not by tech layer

Current sidebar: Overview, Chat, Vision, Hardware, Infrastructure, Security, Models, Settings (7+ items, flat). Flat lists exceed mobile scanning budget.

**Recommended grouping (3 sections, 7 items — same content, better scan):**

- **Work** — Chat, Vision, (add) Tasks/Runs inbox
- **Systems** — Hardware, Infrastructure
- **Governance** — Security, Models, Settings

Header keeps: search / command palette (`⌘K`), approval Badging (dot + count), user avatar. This mirrors `dashboard-01`'s `SiteHeader` + Nuxt Dashboard's `DashboardNavbar` pattern [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks) [Nuxt UI — DashboardPanel](https://ui.nuxt.com/docs/components/dashboard-panel).

### 5.3 Streaming UX: adopt the Vercel tool-state machine end-to-end

1. **Server:** Replace hand-rolled SSE with `ai` package. For the Python harness, stream via `ai-python.dev` (`streamText` → `toUIMessageStream`) or emit AG-UI envelopes that the Next.js route proxies as a UIMessage stream. Set `toolApproval` per tool and `experimental_toolApprovalSecret = env.TOOL_APPROVAL_SECRET` [Vercel — Tool Execution Approval](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).
2. **Client:** `useChat({transport: new DefaultChatTransport({api: '/api/chat'}), sendAutomaticallyWhen: lastAssistantMessageIsCompleteWithApprovalResponses })` and exhaustive `part.state` rendering — including `output-denied` even for tools that didn't require approval [Vercel — Chatbot Tool Usage](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).
3. **Approval UI:** Promote `approval-requested` cards. Auto-decisions render as `Checking approval…` with `isAutomatic` + `reason`; only manual cards show Approve/Deny (calls `addToolApprovalResponse`) [Vercel — Tool Execution Approval](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).
4. **Tool streaming:** Enable `toolCallStreaming` (or `input-streaming` default) and skeleton the card while args stream [Vercel — Chatbot Tool Usage](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage).
5. **Generative pieces:** For Vision, stream a preview card (`<img>` + llava tokens) while mixtral reasons; for research, stream a Sources list.

**Why this matters for SHALLOT:** The current Vision UI was flagged "too sparse". The sparsity is a state-machine gap: vision jumps from "loading" to "done". Streaming `input-streaming` + intermediate `Reasoning` fills the gap without overwhelming.

### 5.4 HITL: typed gates with Pydantic AI → UI envelope → durable audit

Backend (Pydantic AI + Temporal):

```python
# Deferred tools — policy in code, not prompt
@agent.tool(requires_approval=True)  # or conditional via ApprovalRequired
def flash_firmware(image: str, target: str) -> str: ...

# handler is Durable; decisions are DeferredToolResults
result = await agent.run(prompt, deps=deps)
if isinstance(result.output, DeferredToolRequests):
    # serialize with RunState / store in Postgres; UI polls or streams via AG-UI
```

- Use `requires_approval=True` or `raise ApprovalRequired` from `args_validator`/tool body for conditional gates [Pydantic AI — Deferred Tools](https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/).
- Persist via `TemporalAgent` (or DBOS) so approvals survive pod restarts [Pydantic — Durable execution](https://ai.pydantic.dev/durable_execution/overview).
- Log `PostToolUse`-style JSONL to Postgres audit table (tool, input, approval decision, actor, ts) — satisfies the audit requirement without trusting the client [Anthropic — Hooks](https://code.claude.com/docs/en/agent-sdk/hooks).

Frontend envelope (AG-UI shape, renderable by Vercel states):

```json
{"type":"RUN_FINISHED","outcome":{"type":"interrupt","interrupts":[{"id":"approval-1","reason":"tool_call","toolCallId":"call_123","responseSchema":{"properties":{"accepted":{"type":"boolean"},"arguments":{"type":"object"}}}}]}}
```

Resume: `{"threadId":"...","resume":[{"interruptId":"approval-1","status":"resolved","payload":{"accepted":true}}]}` [Microsoft — HITL with AG-UI](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop).

**Approval thresholds:** Keep in Postgres config + Temporal schedule; auto-approve only read-only or `path in /workspace`, never blindly across sessions. Calibrate weekly via approve-rate review (≥99.7% auto-approve → candidate for widening) [Pydantic DeepAgents — Best Practices](https://vstorm-co.github.io/pydantic-deepagents/examples/human-in-the-loop/).

### 5.5 Memory and provenance surfaces

- **Next to Chat:** a collapsible **Execution Timeline** (LangGraph checkpoint pattern): dots per node, amber for interrupts, expand to `values` / `tasks` / `next`, diff between checkpoints [LangGraph — Frontend time-travel](https://docs.langchain.com/oss/python/langchain/frontend/time-travel) [LangGraph — Persistence: checkpointer vs store](https://langchain-ai.github.io/langgraph/concepts/persistence).
- **Global Search:** pgvector-backed memory (Temporal workflows already indexed) surfaced in header command palette; each answer optionally streams `Sources` chips back to chat.
- **Model provenance:** Every assistant message's metadata footer should show: `model@revision` (mixtral, llava:13b → mixtral, NIM vs local), `prompt_id`, `tool manifest version`. This is the Transparency pillar in concrete pixels [arXiv:2601.06223](https://arxiv.org/abs/2601.06223).

### 5.6 Vision (general purpose) page redesign

Replace the breadboard-only view with:

- Drop zone + camera capture (PWA `MediaDevices` + `File System Access` if installed).
- Pipeline stepper: `llava:13b (local)` → `mixtral` (local/NIM/OpenRouter free) — each step is a `Tool` card with its own state; show llava tokens streaming under `input-streaming`.
- Result card: extracted entities, hazards, BOM hints (link to KiCad analyzer), and "use in Chat" action that pre-fills chat with the vision context (Generative UI pattern).
- History table filtered by tag (hardware, docs, field photos).

This satisfies "Vision is general (not just breadboard)" without adding a second dashboard.

### 5.7 PWA polish that makes the Tailscale dashboard feel native

1. **Manifest:** `display: standalone`, `start_url: "/"`, 192/512 maskable icons, `theme_color` matching `globals.css`, `shortcuts` for Chat/Vision/Approvals [web.dev — Installation](https://web.dev/learn/pwa/installation) [MDN — PWAs](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps).
2. **Service worker:** Precache app shell (CSS/JS/fonts) `Cache First`; chat history `Network First`; updated assets `Stale-while-revalidate`; custom offline page "SHALLOT is offline — queued approvals will sync" [web.dev — PWA checklist](https://web.dev/articles/pwa-checklist).
3. **Badging:** Set app badge to pending approval count via Badging API when a `needs-attention` run pauses [MDN — Badging API](https://developer.mozilla.org/en-US/docs/Web/API/Badging_API).
4. **Install prompt:** Respect `beforeinstallprompt`; show a deferred prompt card in Settings/Overview rather than auto-prompting [web.dev — Installation](https://web.dev/learn/pwa/installation).
5. **Responsive QA:** Test with `max-inline-size: 66ch`, `1.5` line-height, `@container` breakpoints; verify sidebar → sheet transform and `DashboardPanel resizable` disabled below `lg` [web.dev — PWA checklist: Responsive](https://web.dev/articles/pwa-checklist) [ui.shadcn.com — Blocks](https://ui.shadcn.com/blocks).

### 5.8 What not to do

- **Don't need full AI Elements or a second UI system.** Add the three AI Elements primitives you need (`Reasoning`, `Tool`, `Sources`) as local shadcn components; they are copy-paste, consistent with block philosophy [ai-sdk.dev — AI Elements](https://ai-sdk.dev/docs/ai-elements).
- **Don't stream thinking for every token on mobile.** Collapse reasoning by default; expand on tap. Reduces over-reliance effect observed in explainability studies [ACM 10.1145/3613905.3638184](https://dl.acm.org/doi/10.1145/3613905.3638184).
- **Don't block the harness on human latency.** The agent run is durable, not blocking a request handler. The UI resumes via stored `threadId/checkpointId`.

---

## Open questions and risks

- **Anthropic `canUseTool` 60 s limit vs long approvals:** Temporal durability solves persistence, but SHALLOT will need a custom approval inbox service that bridges Vercel's client approval to Temporal's resume — verify AG-UI interrupt envelope round-trips through Temporal payloads before committing.
- **Pydantic AI AG-UI + Vercel UIMessage coexistence:** Both claim AG-UI interop; confirm that `ai-python.dev` Python streaming (beta, docs at ai-python.dev) produces Vercel-compatible `toUIMessageStream` bytes that Next.js `DefaultChatTransport` accepts without translation. Fallback is proxy-and-translate via a thin Next.js route.
- **pgvector memory scale:** No load test yet for retrieval latency when chat history + research + hardware logs share one store vs split stores (LangGraph checkpointer/store split recommends split [LangGraph — Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence)).
- **Tailscale + Service Worker scope:** Verify that the Tailscale MagicDNS hostname's scope allows service worker registration at `/` and that `start_url` does not trigger a cross-origin redirect (installability blocker per web.dev).

---

## Sources (primary only)

1. Anthropic — *Building effective agents* (patterns: augmented LLM → workflow → agent). <https://www.anthropic.com/engineering/building-effective-agents>
2. Anthropic — *Effective harnesses for long-running agents*. <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
3. Anthropic Agent SDK — *Overview* (harness packaged as library). <https://code.claude.com/docs/en/agent-sdk/overview>
4. Anthropic Agent SDK — *Permissions* (evaluation order, `canUseTool`, `bypassPermissions`). <https://platform.claude.com/docs/en/agent-sdk/permissions>
5. Anthropic Agent SDK — *Hooks* (`PreToolUse`/`PostToolUse`, audit). <https://code.claude.com/docs/en/agent-sdk/hooks>
6. NPM — `@anthropic-ai/claude-agent-sdk` registry (versions, peers). <https://www.npmjs.com/package/%40anthropic-ai%2Fclaude-agent-sdk>
7. OpenAI — *Agents SDK overview*. <https://developers.openai.com/api/docs/guides/agents>
8. OpenAI — *Guardrails and human review*. <https://developers.openai.com/api/docs/guides/agents/guardrails-approvals>
9. OpenAI Agents SDK Python — *Human-in-the-loop* (interruptions, RunState, alwaysApprove). <https://openai.github.io/openai-agents-python/human_in_the_loop>
10. OpenAI Agents SDK JS — *Human-in-the-loop* (`needsApproval`, flow, preApprovalInputGuardrails). <https://openai.github.io/openai-agents-js/guides/human-in-the-loop>
11. Google ADK — *Tools and Integrations* (central tool registry). <https://google.github.io/adk-docs/tools/>
12. Google ADK Docs — *Function tools — confirmation* canonical (2-min GDE post references this). <https://google.github.io/adk-docs/tools/confirmation/>
13. Google ADK Docs — *Function tools — confirmation* (canonical). <https://google.github.io/adk-docs/tools/confirmation/>
14. Google ADK 2 — *Human input* (RequestInput, response_schema, Beta). <https://google.github.io/adk-docs/workflows/human-input/>
15. Google — *Gemini Enterprise Agent Platform* (ADK placement). <https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents>
16. Microsoft — *Workflows — Human-in-the-loop* (RequestPort, checkpoints, RequestInfoEvent). <https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop>
17. Microsoft — *Using function tools with human-in-the-loop approvals* (ApprovalRequiredFunc, ToolApprovalRequestContent). <https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval>
18. Microsoft — *Human-in-the-Loop with AG-UI* (interrupt envelope, accepted/arguments, batching). <https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop>
19. Vercel AI SDK — *Chatbot Tool Usage* (streamText, useChat, parts, toolApproval). <https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage>
20. Vercel AI SDK — *useChat* (DefaultChatTransport, sendAutomaticallyWhen, addToolApprovalResponse). <https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat>
21. Vercel AI SDK — *Generative UI / AI SDK UI* (streaming, tool states, generative components). <https://ai-sdk.dev/docs/ai-sdk-ui>
22. Vercel AI SDK — *AI Elements* (Conversation, Message, Reasoning, Tool, Sources). <https://ai-sdk.dev/docs/ai-elements>
23. Vercel AI SDK — *Tool Approval* (approval-requested/responded, isAutomatic, experimental_toolApprovalSecret). <https://chatbot.ai-sdk.dev/docs/customization/tool-approval.md>
24. Pydantic AI — *Overview* (one agent, durable execution, UI event streams). <https://ai.pydantic.dev/>
25. Pydantic AI — *Deferred Tools: Human-in-the-Loop Tool Approval* (requires_approval, ApprovalRequired, client-not-a-boundary warning). <https://ai.pydantic.dev/docs/ai/tools-toolsets/deferred-tools/>
26. Pydantic DeepAgents — *Human-in-the-Loop Example* (interrupt_on, DeferredToolRequests, auto-approve safe dirs). <https://vstorm-co.github.io/pydantic-deepagents/examples/human-in-the-loop/>
27. Pydantic AI — *Durable execution* (Temporal/DBOS, HITL built-in). <https://ai.pydantic.dev/durable_execution/overview>
28. Pydantic AI — *Agent-User Interaction (AG-UI) examples*. <https://ai.pydantic.dev/examples/ag-ui>
29. LangGraph — *Human-in-the-loop* (interrupt/Command, patterns: approve/edit/review/validate). <https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop>
30. LangGraph — *Use time-travel* (get_state_history, update_state, forkFrom checkpointId). <https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel>
31. LangGraph — *Time travel (frontend)* (useStream, ThreadState, ampl interrupts, JSON viewer tip). <https://docs.langchain.com/oss/python/langchain/frontend/time-travel>
32. LangGraph — *Persistence* (checkpointer vs store, durable memory). <https://langchain-ai.github.io/langgraph/concepts/persistence>
33. shadcn/ui — *Blocks* (dashboard-01, sidebar-07, SectionCards, ChartAreaInteractive, DataTable). <https://ui.shadcn.com/blocks>
34. shadcn/ui — *Blocks docs* (registry, copy-paste ownership). <https://ui.shadcn.com/docs/blocks>
35. Shadcn Dashboard — *Blocks* (Base UI/Radix, dashboard shells). <https://shadcndashboard.dev/docs/getting-started/blocks>
36. Nuxt UI — *DashboardPanel* (UDashboardPanel, resizable, storage-key). <https://ui.nuxt.com/docs/components/dashboard-panel>
37. Nuxt UI — *Dashboard template* (collapsible sidebar, command palette, light/dark). <https://dashboard-template.nuxt.dev/> and <https://github.com/nuxt-ui-templates/dashboard>
38. MDN — *Progressive Web Apps* (installable, guides, standalone, Badging, Window Controls Overlay). <https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps>
39. web.dev — *What makes a good PWA? Checklist* (responsive, offline page, progressive enhancement). <https://web.dev/articles/pwa-checklist>
40. web.dev — *Installation* (install badge, iOS limitations, beforeinstallprompt). <https://web.dev/learn/pwa/installation>
41. web.dev — *Progressive Web Apps* (explore, capabilities). <https://web.dev/explore/progressive-web-apps>
42. W3C — *Web App Manifest* (spec for installability). <https://www.w3.org/TR/appmanifest/>
43. Cheng et al. — *Toward Safe and Responsible AI Agents: A Three-Pillar Model for Transparency, Accountability, and Trustworthiness* (peer-reviewed conference, 2026-01). <https://arxiv.org/abs/2601.06223>
44. *A Systematic Literature Review of User Trust in AI-Enabled Systems: An HCI Perspective* (arXiv:2304.08795). <https://arxiv.org/abs/2304.08795>
45. *Establishing Appropriate Trust in AI through Transparency and Explainability* (Princeton diss., ACM DOI 10.1145/3613905.3638184, 2024-05). <https://dl.acm.org/doi/10.1145/3613905.3638184>
46. *How Early Adopters Who Build Multi-Agent LLM Systems Conceptualize Transparency* (arXiv:2606.08323). <https://arxiv.org/abs/2606.08323>
47. Vercel — *AI SDK for Python is now in beta* (ai-python.dev). <https://ai-sdk.dev/docs/python> via <https://ai-python.dev/>

---

*Verified against primary sources 2026-08-27. Package versions and pricing are point-in-time; recheck before implementation. ADK Python 2.0 HITL is Beta; Vercel AI SDK Python is Beta; Agent Framework AG-UI is evolving — all flagged as Beta/Open in sources above.*
