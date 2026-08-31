# Ticket D3 — Model reconciliation & vision policy (SHALLOT Harness MVP)

**Research date:** 2026-08-31
**Ticket:** D3 (wayfinder) — Model reconciliation + vision policy
**Scope:** Reconcile the Harness default model (`ministral-3:8b`, ADR 0010) against Cub's
`llama3.2` (ADR 0006); define the `VISION_MODEL` policy; confirm both Ollama tags are real;
confirm how Agno v3 wires a model / a vision model.
**Method:** Primary sources only — repo ADRs + `agno_agent.py`, Ollama library manifests, Agno
official docs (`docs.agno.com`). Point-in-time: Aug 2026.
**Status:** Research only. No code changed. Git is denied in this environment.

---

## Decision (TL;DR)

1. **Harness default model stays `ministral-3:8b`.** It is a real, pullable Ollama tag
   (text+image, 256K ctx, Apache-2.0, ~6.0 GB Q4_K_M).
2. **Vision policy line: `VISION_MODEL=qwen3-vl:8b`** for the stronger general-vision role
   (OCR/spatial/hardware). `qwen3-vl:8b` is a real Ollama tag (text+image, 256K, Apache-2.0,
   ~6.1 GB). In Agno this is wired **per-Agent** (the agent's `model`), not per-tool — see §4.
3. **The Harness↔Cub divergence is intentional and correct — do NOT "harmonize" the models or
   the stacks.** Harness = Agno v3 AgentOS (local-first PM/dev/research agent, broad permissions,
   dev tooling). Cub = Pydantic AI (ADR 0005/0006, operational OT agent, tight trust boundary).
   ADR 0010 explicitly states Cub ADRs 0005–0007 are *not* superseded and remain Cub's concern.
4. **Verification gap (hard):** this environment has **no Ollama and no GPU**. The MVP cannot be
   run or model-verified here. Pulling + tool-call/structured-output validation must happen on
   the RTX 4080 Fedora box (per ADR 0010). Treat this ticket's model choices as *documented
   policy*, not *runtime-verified*.

---

## 1. Recommended model strings

| Env var / role | Recommended value | Source |
|---|---|---|
| `SHALLOT_MODEL` (Harness default) | `ministral-3:8b` | `agno_agent.py:30` (already default), ADR 0010 |
| `VISION_MODEL` (stronger general vision) | `qwen3-vl:8b` | ADR 0010 model table |
| Reasoning A/B (optional, `chain=true`) | `ministral-3:14b` | ADR 0010 |

Both default and vision models are local Ollama tags consumed via `Ollama(id=MODEL_ID)` in
`agno_agent.py:121` (the agent's `model=` argument).

Note: `agno_agent.py` currently reads **only** `SHALLOT_MODEL`. `VISION_MODEL` is named in ADR 0010
but is **not yet wired** in code. Wiring it means either (a) running a dedicated vision Agent with
`model=Ollama(id=os.getenv("VISION_MODEL", ...))`, or (b) making the single model `qwen3-vl:8b`
when stronger vision is wanted. That is an implementation step, out of scope for this research
ticket — recorded here for the follow-up.

---

## 2. Ollama tag verification (both real & pullable)

### `ministral-3:8b` — ✅ real
- Ollama library: `ollama.com/library/ministral-3:8b` — **1.2M downloads**, `6.0GB`, `256K`
  context, **Text, Image input**, arch `mistral3`, params 8.92B, quant Q4_K_M, Apache-2.0.
- `ollama run ministral-3:8b` / `ollama pull ministral-3:8b` are valid (registry manifest
  `registry.ollama.ai/library/ministral-3:8b`).
- Multimodal: "Vision: Enables the model to analyze images …" ([ollama.com/library/ministral-3](https://ollama.com/library/ministral-3)).
- **Requires Ollama ≥ 0.13.1** (per the model readme). Note for the Fedora box: pin Ollama
  version when verifying.

### `qwen3-vl:8b` — ✅ real
- Ollama library: `ollama.com/library/qwen3-vl:8b` — **5.5M downloads**, `6.1GB`, `256K`
  context, **Text, Image input**, arch `qwen3vl`, params 8.77B, quant Q4_K_M, Apache-2.0.
- `ollama run qwen3-vl:8b` / `ollama pull qwen3-vl:8b` valid.
- "The most powerful vision-language model in the Qwen model family to date" ([ollama.com/library/qwen3-vl](https://ollama.com/library/qwen3-vl)); strong OCR / spatial / GUI understanding and agentic tool use.
- **Requires Ollama ≥ 0.12.7**.

Both fit comfortably in the RTX 4080 16 GB VRAM budget (6.0 GB + 6.1 GB) with KV-cache headroom
for 8K–32K context (corroborated by `docs/research/model-selection-rtx4080-2026.md`).

---

## 3. Harness-vs-Cub divergence — why it is correct (no harmonization)

| | Harness (`agno_agent.py`) | Cub (`cub/*.py`) |
|---|---|---|
| Framework | **Agno v3 (AgentOS)** | **Pydantic AI** (ADR 0005/0006) |
| Default model | `ministral-3:8b` | `llama3.2` |
| Role | Standalone PM/dev/research/cybersec/physical-build agent | Operational OT agent (ingress scrubber, router/PDP, egress-deny) |
| Trust boundary | Separate, broad personal perms + dev tooling | Tight OT boundary, sensitive data never leaves perimeter |

Why divergence is correct, not a bug:
- **ADR 0010 is explicit:** "Cub-ADR 0005–0007 supersedas inte; de gäller Cub och behöver separat
  aktualitetsgranskning innan operativ implementation." The Harness runtime swap (Pydantic AI →
  Agno v3, confirmed by owner 2026-08-27) deliberately does **not** rewrite Cub. They are two
  different agents with two different trust boundaries.
- **Different optimization targets.** Cub is inference-architecture-locked for data-minimization,
  scrubbing, and policy-routed egress (ADR 0006). The Harness is a local-first productivity agent
  where `ministral-3:8b` (Apache-2.0, 256K, vision+tools) is the chosen generalist.
- **`llama3.2` in Cub is not "wrong"** just because the Harness uses `ministral-3`. It is a
  separate stack decision. Recommending "use the same model" would couple two unrelated agents
  and is rejected by ADR 0010's separation principle.

**Ruling for the ticket:** Divergence is intentional. No harmonization. Keep `ministral-3:8b` for
the Harness, keep Cub's stack/model as Cub's own concern.

---

## 4. Agno v3 model & vision wiring

- **How a model is set on an Agent (per-Agent):** Agno sets the model on the `Agent` (or `Team`)
  via the `model=` argument — `Agent(model=Ollama(id="ministral-3:8b"), ...)`. The model class
  selects the provider API; `id` selects the model/tag. ([docs.agno.com/models/introduction](https://docs.agno.com/models/introduction))
- **Vision / multimodal is per-Agent, not per-tool.** Agno passes media to the agent's
  `run()`/`print_response()` via `images=[Image(...)]`, `videos=[...]`, `audio=[...]`,
  `files=[...]`. The agent's *own* model must be multimodal-capable; there is **no native
  per-tool vision-model override** for input analysis. ([docs.agno.com/multimodal/agent/overview](https://docs.agno.com/multimodal/agent/overview), [docs.agno.com/input-output/multimodal](https://docs.agno.com/input-output/multimodal))
- **Exception — image *generation* tools only:** image-output tools (e.g. `OpenAITools`) accept a
  separate `image_model="..."` for *generation*, which is unrelated to vision *input* analysis.
- **Consequence for `VISION_MODEL`:** because vision is per-Agent in Agno, `VISION_MODEL` should
  be the model id of a dedicated vision Agent (or the single agent's model when stronger vision is
  desired). ADR 0010's "single-model chain (vision+reasoning in same VLM) is default" maps
  cleanly onto Agno's per-Agent model: pick one multimodal model. `qwen3-vl:8b` is the
  recommended stronger-vision pick; `ministral-3:8b` already covers vision+reasoning as default.

---

## 5. Verification gap (must read before sign-off)

- **This environment has no Ollama and no GPU.** `ministral-3:8b` and `qwen3-vl:8b` could **not**
  be pulled, loaded, or tool-call-tested here.
- **Tag existence was verified against Ollama's public library manifests only** (web), not by a
  local `ollama pull`. Existence ≠ runtime fitness.
- **Required verification (RTX 4080 Fedora box, per ADR 0010):**
  1. `ollama pull ministral-3:8b` and `ollama pull qwen3-vl:8b` (pin Ollama ≥ 0.13.1 / ≥ 0.12.7).
  2. Confirm VRAM fit (6.0 GB + 6.1 GB) at intended `num_ctx`.
  3. Validate **tool-calling + structured output** on both (ADR 0010 calls this out as the
     production gate). The Harness's HITL tools (`approve_action`, `run_harness`) depend on
     reliable tool calls.
  4. Wire `VISION_MODEL` into `agno_agent.py` (currently unread) and smoke-test image input.
- **MVP cannot be verified in this environment.** Treat D3's outputs as documented policy; the
  runtime sign-off belongs on the Fedora box.

---

## Sources
- Repo: `agno_agent.py` (SHALLOT_MODEL default, Ollama wiring), `docs/adr/0010-standalone-shallot-harness.md`, `docs/adr/0006-cub-agent-inference-architecture.md`, `cub/config/__init__.py` (`llama3.2`), `docs/research/model-selection-rtx4080-2026.md`.
- Ollama: `ollama.com/library/ministral-3:8b`, `ollama.com/library/qwen3-vl:8b`, `registry.ollama.ai/library/ministral-3:8b`, `registry.ollama.ai/library/qwen3-vl:8b`.
- Agno: `docs.agno.com/models/introduction`, `docs.agno.com/multimodal/agent/overview`, `docs.agno.com/input-output/multimodal`.
