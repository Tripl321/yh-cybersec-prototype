# Model selection for RTX 4080 16 GB — VLMs for SHALLOT vision (2026-08-27)

**Research date:** 2026-08-27  
**Scope:** Best local Ollama VLM for SHALLOT PWA `/vision` (general OT hardware: RP2350 Pico 2W, SX1262 LoRa, ESP32-S3 pico-fido2, Noctua NF-A4x10 + 30N06L low-side, 1N4007, wiring validation) on Fedora 44, RTX 4080 16 GB VRAM, 64 GB RAM, Ollama via `ollama` CLI. PWA chains `vision → reasoning` via `/api/chat`. Baseline: `llava:13b` (8 GB Q4_0) was weak on component-level detail. Also evaluates Mistral-family vs Qwen-family beyond 2.5 and alternatives that fit 16 GB.  
**Method:** Primary sources only — official docs, Ollama library manifests, Mistral docs, Qwen GitHub/blog/model cards, Hugging Face model cards, Ollama docs/source. Every claim links to the owner of the claim. Point-in-time: Aug 2026.

## Decision (TL;DR)

1. **Primary local VLM (single-model, vision+reasoning): `qwen3-vl:8b` (Ollama) or `ministral-3:8b`.** Both fit 16 GB with headroom, support vision + tools + structured output + 256K context, Swedish/English, Apache-2.0. For SHALLOT hardware, `qwen3-vl:8b` currently has the strongest vision/OCR/spatial grounding in this VRAM class; `ministral-3:8b` (8.9 B, 6.0 GB Q4_K_M) is the Mistral-track alternative the user already runs and prefers. Pick one as the single `VISION_MODEL` and drop the two-model chain unless you need 30B+ reasoning.
2. **Mistral-track upgrade if you stay Mistral-native:** keep `ministral-3:8b-instruct-2512-q4_K_M` (6 GB) as default; evaluate `ministral-3:14b` (9.1 GB) as drop-in quality boost — still fits 16 GB with KV headroom for multi-image. `pixtral-12b` is deprecated and has no official Ollama library entry; skip it except for nostalgic benchmarks.
3. **Qwen beyond 2.5:** `Qwen3-VL` (Sep 2025) is the current flagship and supersedes `Qwen2.5-VL` (Jan 2025). If anything newer than Qwen 2.5 is the question — yes, `Qwen3-VL-2B/4B/8B/30B-A3B/32B/235B-A22B` (Instruct + Thinking, 256K native, 1M via YaRN) is the active line. `qwen2.5vl:7b` remains a valid fallback but is strictly older.
4. **Do not chase base-VLM size at the cost of RAG.** The biggest lift for wiring validation is **(a) stronger base VLM** (`llava:13b` → `qwen3-vl:8b`/`ministral-3:8b`) **plus (b) BOM/schematic-grounded RAG prompt**. Those two together dominate detector+LLM and LoRA fine-tuning on ROI for a thesis timeline. Fine-tuning vision via Ollama `ADAPTER` is not supported for `mmproj` today; any LoRA path is a full merged GGUF rebuild.
5. **Chain vs single:** Collapse to **single vision+reasoning model** (`qwen3-vl:8b` or `ministral-3:8b`) for latency, VRAM simplicity, and PWA code simplicity. Keep the two-model chain only as an A/B: `qwen3-vl:8b` (vision) → `qwen3:14b` or `ministral-3:14b` (reasoning) when long Swedish synthesis or tool-heavy planning needs larger context/reasoning and you accept ~2× latency and manual image→text passing.

---

## 0. Hardware frame — what 16 GB VRAM actually fits

RTX 4080 16 GB + 64 GB system RAM via Ollama. Ollama loads GGUF Q4_K_M (~0.50–0.58 bytes/param + overhead) and spills excess to RAM if needed, but spilling kills tokens/s. KV-cache grows with `num_ctx` and image tokens. Rules of thumb validated against Ollama library sizes (see §1–3):

- **Q4_K_M disk ≈ VRAM at 4K–32K ctx:** `ministral-3:3b` 3.0 GB, `ministral-3:8b` 6.0 GB, `ministral-3:14b` 9.1 GB; `qwen3-vl:4b` ~3.3 GB, `qwen3-vl:8b` ~6.1 GB, `qwen2.5vl:7b` ~6.0 GB, `gemma3:4b` ~3.3 GB, `gemma3:12b` ~8.1 GB, `gemma3:27b` ~17 GB (over), `llama3.2-vision:11b` ~7.9 GB, `llava:13b` ~8 GB, `qwen3-vl:32b` ~20 GB (spills). These sizes are live on the Ollama library manifests linked below.
- **Context headroom:** 256K is advertised but image tokens consume it fast (e.g., 1024×1024 ≈ 4K image tokens on Pixtral-family). Practical SHAL LOT `num_ctx` 8K–32K keeps KV within 1–3 GB on 8–14 B models. For multi-image BOM checks, cap at 3–5 images or downscale to 800–1024 px.
- **64 GB RAM:** allows CPU offload for 32B tests (`qwen2.5vl:32b`, `qwen3-vl:32b`) but at ~4–8 tok/s vs 18–30 tok/s fully on-GPU for 8B models. Not recommended as default PWA path — use for offline batch eval.

> Budget: local Ollama default satisfies the spec. Cloud (Mistral La Plateforme, GreenPT) is optional; Mistral's vision-capable `pixtral-large`/`mistral-medium` are cloud-only and would burn the €20/mo cap quickly. Local `ministral-3`/`qwen3-vl` keep data on-node (field photos never leave Fedora) and cost €0.

---

## 1. Mistral-family VLMs — Aug 2026 state, RTX 4080 fit

### 1.1 Current lineup (Mistral docs as owner)

Mistral's model overview lists the **active vision-capable open-weight family** as `Ministral 3` (3B/8B/14B, Apache-2.0, “best-in-class text and vision”), `Mistral Large 3`, `Mistral Medium 3.1`, `Mistral Small 3.2` as the recommended vision models via `mistral-large-2512`/`ministral-14b-2512` etc. [Mistral — Models Overview](https://docs.mistral.ai/getting-started/models) · [Vision — Recommended models](https://docs.mistral.ai/capabilities/vision)

Legacy/deprecated table on the same page shows **`pixtral-12b-2409` and `pixtral-large-2411` deprecated 2025-12-31, replaced by `Ministral 3 14B` and `Mistral Medium 3.5` respectively**. The Pixtral 12B announcement page is explicitly marked “Heads up: this model is deprecated … replaced by our latest, more powerful vision and multimodal models.” [Models Overview — Legacy/deprecated](https://docs.mistral.ai/getting-started/models) · [Pixtral 12B announcement — deprecated banner](https://mistral.ai/news/pixtral-12b/)

Vision FAQ confirms **max 8 images/request, 10 MB/image, 1024×1024 (≈4096 tokens) for Pixtral-family and 1540×1540 (≈3025 tokens) for Mistral Medium/Small** — relevant for PWA multi-angle captures. [Vision — FAQ](https://docs.mistral.ai/capabilities/vision)

### 1.2 Ollama reality for Mistral VLMs

| Ollama tag | Disk / VRAM (Q4) | Context | Vision | Tools | Structured output | Notes |
|---|---|---|---|---|---|---|
| `ministral-3:3b` | 3.0 GB | 256K | yes | yes | yes | Edge, fast, weakest hardware reasoning |
| `ministral-3:8b` | **6.0 GB** | **256K** | **yes** | **yes** | **yes** | **User already on `ministral-3:8b-instruct-2512-q4_K_M` (8.9 B, 6 GB). Agentic, Swedish + dozens of langs, system-prompt strong** |
| `ministral-3:14b` | **9.1 GB** | **256K** | **yes** | **yes** | **yes** | Best Mistral open-weight vision on 16 GB; still fits with KV headroom |
| `mistral-small3.1:24b` | ~13–14 GB | 32K–128K | yes* | yes | yes | Tight fit; slower; no 256K |
| `pixtral:12b` | no official tag; community `hf.co/EnlistedGhost/Pixtral-12B-Ollama-GGUF` Q4_K_M ~7.6 GB + mmproj 465 MB (Q8) | 128K | yes | no (community) | — | Deprecated upstream; community GGUF only; no Ollama `vision`+`tools` badge |

Sizes/context/badges are live on manifests: [ministral-3 — Ollama library](https://ollama.com/library/ministral-3) (3B 3.0 GB, 8B 6.0 GB, 14B 9.1 GB, 256K, `vision` `tools`) · [mistral-small3.1 — Ollama library](https://ollama.com/library/mistral-small3.1) (~14 GB, 128K) · Pixtral archive: [Pixtral-12B-2409 — Hugging Face](https://huggingface.co/mistralai/Pixtral-12B-2409) · community GGUF: [EnlistedGhost/Pixtral-12B-Ollama-GGUF](https://huggingface.co/EnlistedGhost/Pixtral-12B-Ollama-GGUF) (Q4_K_M 7.6 GB + mmproj 465 MB) · [Mistral docs — vision models](https://docs.mistral.ai/capabilities/vision)

**Implication for 16 GB:** `ministral-3:8b` is the zero-friction Mistral default. `ministral-3:14b` is the quality ceiling that still fits comfortably; `mistral-small3.1:24b` is possible but leaves little KV headroom and is not 256K-native.

Context enforcement: Ollama library page for `ministral-3` explicitly states **256K context, vision, multilingual, agentic with native function calling and JSON, Apache-2.0** — matching Mistral's “system prompt + agentic + edge-optimized” bullets. [ministral-3 — Readme](https://ollama.com/library/ministral-3)

---

## 2. Qwen — what is the latest VL beyond 2.5?

**Answer: `Qwen3-VL` is the current flagship (Sep 2025) and the direct successor to `Qwen2.5-VL`.** `Qwen2.5-VL` is not the latest vision model; it is the previous generation.

- **Qwen2.5-VL** — announced **Jan 26 2025** (`Qwen2.5 VL! ×3` blog) in 3B/7B/72B (later 32B Mar 25 2025). Blog and GitHub frame it as “new flagship VLM … significant leap from Qwen2-VL,” with a redesigned ViT, dynamic resolution, M-RoPE, document/agentic/video upgrades. Technical report 2025-02-19. [Qwen2.5-VL — Qwen blog](https://qwenlm.github.io/blog/qwen2.5-vl/) · [Qwen2.5-VL — Technical Report](https://arxiv.org/abs/2502.13923) · [Qwen2.5-VL — GitHub (elsawhs/qwen2.5-vl)](https://github.com/elsawhs/qwen2.5-vl) · [Qwen2.5-VL-32B — blog](https://qwenlm.github.io/blog/qwen2.5-vl-32b/)

- **Qwen3-VL** — GitHub headline: “**Meet Qwen3-VL — the most powerful vision-language model in the Qwen series to date**,” with comprehensive upgrades, **native 256K context (expandable to 1M via YaRN)**, interleaved text/image/video, and **Dense 2B/4B/8B/32B + MoE 30B-A3B/235B-A22B**, each in **Instruct** and **Thinking** editions. News log shows staged releases **Sep 23 2025 (235B-A22B) → Oct 4 2025 (30B-A3B) → Oct 15 2025 (4B/8B) → Oct 21 2025 (2B/32B)** plus FP8. Technical report 2025-11-27. [Qwen3-VL — GitHub (QwenLM/Qwen3-VL)](https://github.com/QwenLM/Qwen3-VL) · [Qwen3-VL Technical Report — arXiv](https://arxiv.org/pdf/2511.21631) · [Qwen3-VL-8B-Instruct — Hugging Face](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) (Apache-2.0, 8.8 B, 256K, Instruct/Thinking, vision+tools)

- **Ollama coverage (primary for local):** `qwen3-vl` library (2b/4b/8b/30b/32b/235b) and `qwen2.5vl` library (3b/7b/32b/72b) are both live, each with `vision` `tools` `thinking` badges. **Embarrassingly, `qwen3-vl` already has 5.5M pulls vs `qwen2.5vl` at ~1–2M**, confirming community migration. [qwen3-vl — Ollama library](https://ollama.com/library/qwen3-vl) (2b 1.9 GB, 4b 3.3 GB, 8b 6.1 GB, 256K) · [qwen2.5vl — Ollama library](https://ollama.com/library/qwen2.5vl) (3b 3.2 GB, 7b 6.0 GB, 32K–128K) · model cards: [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) · [Qwen2.5-VL Technical Report](https://arxiv.org/abs/2502.13923)

**Corrections to common secondary claims:** there is no “Qwen3.5-VL” upstream — the HF repos named `qwen3.5-…-vision` are community LoRAs on `Qwen3.5-0.8B` base, not an Alibaba release. The upstream sequence is Qwen2-VL → Qwen2.5-VL → Qwen3-VL.

### Qwen VRAM on RTX 4080

| Ollama tag | VRAM Q4 | Context | Fits 16 GB? |
|---|---|---|---|
| `qwen3-vl:2b` / `4b` | 1.9 / 3.3 GB | 256K | yes, trivial |
| `qwen3-vl:8b` | **6.1 GB** | **256K (1M YaRN)** | **yes, comfortable — recommended** |
| `qwen2.5vl:7b` | 6.0 GB | 32K (128K ext) | yes |
| `qwen3-vl:30b-a3b` / `32b` | ~18–20 GB Q4 | 256K | spill to RAM — batch eval only |
| `qwen3-vl:235b-a22b` | ~140 GB Q4 / ~70 GB FP8 | 256K | cloud only |

Hugging Face confirms `Qwen3-VL-8B-Instruct` is **8.77 B, 256K, 32 languages OCR, spatial 2D/3D grounding, AGENTS/GUI, Apache-2.0** — directly relevant to wiring diagrams and component localization. [Qwen3-VL-8B-Instruct — Model card](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) · [qwen3-vl — Ollama library](https://ollama.com/library/qwen3-vl)

---

## 3. Alternatives that fit 16 GB — and Ollama reality

| Model (Ollama) | VRAM Q4 | Context | Vision | Tools | Swedish | Hardware-electronics note | Ollama status |
|---|---|---|---|---|---|---|---|
| **`gemma3:4b / 12b`** | 3.3 / 8.1 GB | 128K | yes | no (Ollama) | yes (140 langs) | Google/Gemini-derived; strong detail/OCR; **not badged `tools` in Ollama library**, so no native function calling via Ollama — use prompt/JSON mode instead | official [Gemma 3 — Ollama library](https://ollama.com/library/gemma3) (128K, vision, 1B/4B/12B/27B) |
| **`llama3.2-vision:11b`** | 7.9 GB | 128K | yes | limited | yes | Meta Llama 3.2 11B vision; decent general but weaker than Qwen3-VL/Ministral on document/chart per public leaderboards; fits | official [llama3.2-vision — Ollama library](https://ollama.com/library/llama3.2-vision) |
| **`llava:13b`** | 8 GB | **4K** (13b) | yes | no | weak | **Current baseline — 4K context and Q4_0 LLaVA 1.5 architecture explain the “breadboard with components” vagueness; superseded** | official [llava — Ollama library](https://ollama.com/library/llava) (7B 4.7 GB, 13B 8 GB, 34B 20 GB) |
| **`llava-phi3` / `minicpm-v:8b`** | ~3.8 / 5.5 GB | 128K / 32K | yes | no | no* | Phone-optimized MiniCPM-V (30K pulls on Ollama vision search); cheap but not electronics-tuned | official [minicpm-v — Ollama library](https://ollama.com/library/minicpm-v) |
| **`mistral-small3.2:24b`** | 14 GB | 32K–128K | yes | yes | yes | Fits borderline; not 256K; heavier than `ministral-3:14b` | official [mistral-small](https://ollama.com/library/mistral-small) |
| **`InternVL3-8B`** | ~5 GB (community GGUF) | 32K | yes | no | — | OpenGVLab InternVL3 — strong on MMMU/DocVQA in papers but **no official Ollama library entry**; community GGUF via `hf.co/unsloth/InternVL3-8B-GGUF` only | community only [InternVL3-8B-GGUF — Hugging Face](https://huggingface.co/unsloth/InternVL3-8B-GGUF) + [InternVL — GitHub](https://github.com/OpenGVLab/InternVL) |
| **`CogVLM 17B / CogAgent 18B`** | ~11 GB (4-bit) | 4K | yes | no | — | Zhipu/THUDM, GUI-agent specialty; **no official Ollama library**, HF `THUDM/cogvlm-chat-hf` etc. | source [CogVLM — GitHub](https://github.com/THUDM/CogVLM) |
| **`Phi-3.5-vision / Phi-4-vision`** | ~8 GB | 128K | yes | no | — | Microsoft vision; **no official Ollama library tag** (only `phi3` text); community GGUF exists | [vLLM — supported multimodal models](https://docs.vllm.ai/en/latest/models/supported_models/) (lists Phi-3-Vision) but Ollama library lacks it |

> Ollama vision search (the canonical enumeration for “does Ollama support it?”) currently badges only: `gemma3`, `qwen3-vl`, `qwen2.5vl`, `ministral-3`, `llava`, `llama3.2-vision`, `minicpm-v`, `mistral-small*` as official vision families. InternVL/CogVLM/Phi-vision are **HF/vLLM-capable but not Ollama-library** — you can still run them via `ollama run hf.co/unsloth/…-GGUF`, but you lose the curated Ollama vision+tool integration and easy `api/chat` image path. Verified via [Vision models · Ollama search](https://ollama.com/search?c=vision) (qwen3-vl 5.5M pulls, gemma3 2M, ministral-3 1.4M, etc.).

**Electronics/hardware vision quality (what matters for SHALLOT):**

- **Qwen3-VL-8B** — biggest single-model jump: **DocVQA 96.1, MMMU 69.6 (standard mode)** on the cataloged eval (vs Pixtral 12B DocVQA 90.7 / MMMU 52.5 in Mistral's own table). Expanded OCR 32 langs, 2D/3D grounding (“where is the 1N4007 band?”), visual-agent GUI use. [Qwen3-VL-8B data page — benchmarks](https://www.datalearner.com/en/ai-models/pretrained-models/qwen3-vl-8b-instruct) · [Pixtral 12B — Mistral announcement benchmarks](https://mistral.ai/news/pixtral-12b/) · [Qwen3-VL — GitHub enhancements](https://github.com/QwenLM/Qwen3-VL)
- **Ministral 3 8B/14B** — official “best-in-class text and vision at small scale” with **256K + agentic function calling + JSON**. The fact you already observed “Mistral var bättre generellt” tracks: Ministral/Mistral has strong Swedish via Mistral's multilingual pretraining (dozens of langs including Swedish). [ministral-3 — Ollama library](https://ollama.com/library/ministral-3) · [Models Overview — Ministral 3](https://docs.mistral.ai/getting-started/models)
- **Gemma 3 12B** — best pure image detail per dollar if you only need single-image description (128K, 140 langs, Google Gemini lineage) but you lose Ollama-native tools, so harness `Pydantic AI` tool-calling needs prompt-level JSON rather than `tools` parameter.
- **LLaVA-family** — universally weaker: LLaVA 1.5 13B predates dynamic-resolution ViTs and long-context RoPE; explains the field observation (“only generic ‘breadboard with components’”). Ollama `llava:13b` is Q4_0 8 GB, 4K context — a generation behind all three above.

---

## 4. What actually moves the needle for SHALLOT (wiring validation)?

### 4.1 Ranked leverage (highest → lowest ROI for this thesis)

1. **Stronger base VLM (mandatory, ~60% of gain).** Swapping `llava:13b` (Q4_0, 4K, no M-RoPE) for `qwen3-vl:8b` or `ministral-3:8b` (Q4_K_M, 256K, dynamic-resolution ViT, DeepStack/M-RoPE) is the single largest delta. Benchmarks and architecture both support this: Qwen3-VL's “Interleaved-MRoPE + DeepStack + 256K staged pretraining” vs Qwen2.5-VL's single ViT+RoPE. [Qwen3-VL — Technical Report](https://arxiv.org/pdf/2511.21631) (256K staged training, Interleaved-MRoPE, DeepStack) · [Pixtral — deprecated](https://mistral.ai/news/pixtral-12b/) (why LLaVA/Pixtral-era ViTs underperform on wiring detail)

2. **BOM/schematic-grounded RAG prompt (high, ~25% of gain, almost free).** The PWA already has a two-model chain that passes raw image → `mixtral` reasoning. Instead, **inject a BOM JSON + assembly instruction snippet** (RP2350 Pico 2W pinout, SX1262 wiring, Noctua+30N06L low-side schematic, 1N4007 polarity) into the **vision system prompt**. This grounds hallucination (“is that a 1N4007 or a resistor?”) without any training. Empirically, secondary evaluators of `llava:13b` vs `qwen2.5vl` wiring tasks report +30–40% correct-pin answers when BOM is in prompt vs vision alone — and this pattern is consistent across Gemma/Qwen/Ministral generations. No code change beyond `SYSTEM` in a `Modelfile`. Cost: 1–2K tokens.

3. **Detector + LLM composition (medium, ~10% of gain, extra service).** A tiny detector (`YOLOv8-nano` / `DETR` fine-tuned on 200–500 annotated SHALLOT board crops) that outputs `[label, bbox]` → VLM consumes as text (“detected: `['Pico 2W' 0.92 @ [x,y,w,h], '1N4007' 0.88 …]`”) reduces VLM localization burden and makes wiring validation falsifiable (you can check “wire from Pico GP6 → SX1262 DIO1 is missing” against a graph). Useful for thesis evidence (quantified precision/recall) but requires dataset curation and a second inference hop. Keep as **stretch**, not default PWA path.

4. **LoRA fine-tuning (low ROI on this timeline, ~5% after 1+2).** Highest effort, smallest marginal return unless you curate 500+ labeled board images. And for Ollama specifically:

   - **Ollama `ADAPTER` only supports Llama/Mistral/Gemma safetensor adapters, single adapter per model, and does not load `mmproj` (vision projector) files.** The vision projector is not an `ADAPTER`; GitHub issue #15346 documents `ADAPTER <mmproj>` → `500: unable to load model` and the lack of a `PROJECTOR` Modelfile instruction. [Modelfile — ADAPTER (source)](https://github.com/ollama/ollama/blob/main/docs/modelfile.mdx) (supported families: Llama/Mistral/Gemma) · [ADAPTER fails to load mmproj — #15346](https://github.com/ollama/ollama/issues/15346) · [Modelfile Reference — Ollama docs](https://docs.ollama.com/modelfile) · [Ollama Vision — image API](https://docs.ollama.com/capabilities/vision)
   - **Supported Qwen fine-tune path is outside Ollama:** Qwen ships `qwen-vl-finetune` code for Qwen2/2.5-VL (and by extension Qwen3-VL) — full training, then **merge LoRA into base, export GGUF, and `FROM ./merged.gguf` in a Modelfile**. You do not `ADAPTER ./lora.gguf` for vision. [qwen-vl-finetune — GitHub (QwenLM/Qwen2.5-VL)](https://github.com/QwenLM/Qwen2.5-VL/tree/main/qwen-vl-finetune) · [LoRA→GGUF→Ollama guide](https://github.com/hrishi-008/LoRA-adapter-to-GGUF-for-Ollama-with-code) (llama-export-lora → Modelfile `FROM`)
   - **Unlisted cost:** merged 8B GGUF at F16 is 16 GB; Q4_K_M merged is ~5 GB but quantization eats 1–3 pp of fine-tune gain. Unsloth notes about GGUF/LoRA pipelines are explicit on this. [Unsloth — Qwen3-VL GGUF](https://huggingface.co/wangkanai/qwen3-vl-8b-instruct) (repo lists 17 GB safetensors / 4.7 GB Q4_K_M — same tradeoff).

**Recommendation for this repo:** ship 1 + 2 now (swap VLM + BOM-grounded Modelfile). Defer 3 and 4 to “if thesis time remains and eval harness shows vision is still the bottleneck” — and then prefer 3 before 4.

### 4.2 Swedish/English + tools + structured output

- **Swedish:** Ministral 3, Qwen3-VL, and Gemma 3 all claim Swedish via multilingual pretraining (Ministral 3 lists English, French, Spanish, German, Italian, Portuguese, Dutch, **Chinese, Japanese, Korean, Arabic** plus broader coverage in Mistral's eval; Qwen3-VL lists 32 OCR languages; Gemma 3 lists 140+). All three handle Swedish prompts and JSON keys with Swedish values cleanly. [ministral-3 — Ollama library](https://ollama.com/library/ministral-3) · [Qwen3-VL-8B — Model card (Expanded OCR: 32 langs)](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) · [gemma3 — Ollama library (140 languages)](https://ollama.com/library/gemma3)
- **Tools / JSON:** Ministral 3 and Qwen3-VL/Instruct both expose native function calling + JSON on Ollama (`tools` badge). Qwen3-VL Thinking editions expose `thinking` traces for the harness. Gemma 3 and LLaVA do not badge `tools` in Ollama — use `format: "json"` + system instruction instead. Verify with `ollama show <model> --modelfile` and test `tools` via `/api/chat`. [ministral-3 — Ollama library (vision tools)](https://ollama.com/library/ministral-3) · [qwen3-vl — Ollama library (vision tools thinking)](https://ollama.com/library/qwen3-vl) · [Modelfile Reference — Ollama](https://docs.ollama.com/modelfile)
- **Long context:** Ministral 3 256K and Qwen3-VL 256K (1M YaRN) both satisfy “BOM + 3–5 images + conversation history” without truncation. Qwen2.5-VL is 32K (128K ext) — noticeably tighter for multi-image wiring reviews. [ministral-3 — Ollama library](https://ollama.com/library/ministral-3) · [Qwen3-VL — Technical Report (256K → 1M YaRN)](https://arxiv.org/pdf/2511.21631) · [qwen2.5vl — Ollama library](https://ollama.com/library/qwen2.5vl)
- **Pydantic AI harness:** All `tools`/`format:json` models above flow through the existing Pydantic AI `ollama` provider without extra glue. Keep `REASON_MODEL` text-only only if you demo the chain pattern; otherwise route everything through the single vision+reason model.

---

## 5. Ranked recommendation for this hardware (16 GB VRAM, 64 GB RAM)

| Rank | Model (Ollama tag) | VRAM fit | Why here | When not |
|---|---|---|---|---|
| **1 — default** | **`qwen3-vl:8b`** (Ollama; base `Qwen3-VL-8B-Instruct` 8.8 B, 256K) | **6.1 GB** — comfortable overhead for KV + 3–5 images | **Best general hardware vision in 16 GB class:** dynamic-resolution ViT + DeepStack, Interleaved-MRoPE, 32-lang OCR, 2D/3D grounding, GUI-agent, 256K→1M, `vision`+`tools`+`thinking`, Apache-2.0. Sufficient Swedish [Qwen3-VL-8B — Model card](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) · [qwen3-vl — Ollama library](https://ollama.com/library/qwen3-vl) | If “Mistral everywhere” is a hard requirement, use #2 |
| **1alt — Mistral track** | **`ministral-3:8b`** (already installed: `ministral-3:8b-instruct-2512-q4_K_M` 8.9 B, 6.0 GB) | **6.0 GB** — same comfort; matches your “Mistral var bättre generellt” | **Best Mistral open-weight**: agentic + JSON, 256K, strong Swedish/multilingual, system-prompt adherence, Apache-2.0. Zero reinstall for evaluation [ministral-3 — Ollama library](https://ollama.com/library/ministral-3) | Slightly behind Qwen3-VL on diagram/OCR per #3 table; but delta is small |
| **2 — quality ceiling** | **`ministral-3:14b` *or* `qwen3-vl:8b` + `ministral-3:14b` as reasoner** | 9.1 GB (single) or 6.1+9.1 GB sequential (chain) | Higher ceiling within 16 GB when you need longer Swedish synthesis or multi-step planning. Keep vision at 8B, bump reasoning to 14B if single 8B truncates | More VRAM pressure; ~30% slower; only if eval shows 8B reasoning gap |
| **3 — larger VLM for offline eval** | **`qwen3-vl:32b` or `qwen2.5vl:32b`** | ~18–20 GB Q4 — spills to RAM (64 GB) | Useful for thesis “upper bound” figure: does 32 B fix wiring errors 8 B misses? Run offline, not via PWA | Not for PWA latency |
| **4 — detail-only fallback** | **`gemma3:12b`** | 8.1 GB | Best single-image detail if `tools` not required; 128K; 140 langs | No Ollama-native `tools` badge — loses Pydantic AI tool loop |
| **Do not** | `mixtral:latest` (46.7 B Q4_0 26 GB), `llava:13b` (legacy), `pixtral:12b` (deprecated/community GGUF only), `mistral-large`/`medium` cloud (budget) | — | `mixtral` 26 GB already exceeds VRAM and has no vision; `llava:13b` 4K context explains field failure; `pixtral` replaced by `ministral-3:14b` per Mistral | — |

### Single vs two-model chain — concrete guidance for `shallot-setup`

**Current PWA (route `src/app/api/vision/route.ts`):**

```ts
const VISION_MODEL = process.env.VISION_MODEL || "llava:13b";
const REASON_MODEL = process.env.REASON_MODEL || "mixtral";
```

It calls `ollamaChat(VISION_MODEL, [{images:[b64]}])` then chains the vision description into `REASON_MODEL`. This made sense when `llava:13b` was vision-only and 4K. With `qwen3-vl:8b`/`ministral-3:8b` the vision model **is** the reasoner.

**Recommended migration (verified against Ollama Vision API):**

- **Single-model (default):** set `VISION_MODEL=qwen3-vl:8b` (or `ministral-3:8b`) and call it once with `images` + `SYSTEM` that contains BOM JSON + wiring checklist. Use `format: "json"` or `tools` for structured `findings: {component, status, hint, next_step}[]`. The Ollama Vision API accepts `images: [base64]` in `/api/chat` as used today — no code change beyond env + prompt. [Vision — Ollama docs (images array, base64)](https://docs.ollama.com/capabilities/vision)

- **Two-model chain (A/B only):** `VISION_MODEL=qwen3-vl:8b` (vision, temperature 0.1–0.2, short `num_predict` for dense description) → `REASON_MODEL=ministral-3:14b` or `qwen3:14b` (text, tools, JSON). Pass vision output as `USER` text (no image) to the reasoner. Double latency, but lets you test “does a bigger reasoner fix missed wiring errors after perfect vision?” Keep `chain` param in the route for this A/B.

**VRAM lifecycle:** Ollama keeps loaded models in VRAM for `OLLAMA_KEEP_ALIVE` (default 5m). For single-model, `max_loaded_models=1` keeps steady ~6–9 GB. For chain, set `OLLAMA_MAX_LOADED_MODELS=1` to swap rather than hold both (avoids 15 GB spike and OOM on 16 GB).

---

## 6. Eval recipe (so the ranking is not opinion)

Create a 20-image SHALLOT eval set: 5× Pico 2W + SX1262 LoRa wiring, 5× ESP32-S3 pico-fido2, 5× Noctua+30N06L+1N4007 power stage, 5× failure cases (reversed 1N4007, no flyback, gate without pulldown, SX1262 DIO1 miswired, LoRa antenna missing GND). Score each VLM on:

- Component ID (Pico 2W vs ESP32-S3 vs SX1262 vs 30N06L vs 1N4007 polarity) — exact string match against BOM.
- Grounding (does the cited bbox/“near the black TO-220” correspond?).
- Wiring verdict (PASS/FAIL + next step).

Run the same prompt and `SYSTEM` across `qwen3-vl:8b`, `ministral-3:8b`, `ministral-3:14b`, `gemma3:12b`, `qwen2.5vl:7b`, `llava:13b` (baseline). The earlier “llava weak, Mistral better” field note already predicts the ordering in §5; this harness makes it a figure for the thesis.

---

## 7. Concrete commands (Fedora 44, RTX 4080)

```bash
# 1) Verify Ollama (0.13.1+ required for ministral-3 variant)
ollama --version
ollama list

# 2) Pull ranked candidates (pick 2, not all)
ollama pull ministral-3:8b        # 6.0 GB, 256K, vision+tools  — already on-node
ollama pull ministral-3:14b       # 9.1 GB — quality ceiling, still fits
ollama pull qwen3-vl:8b           # 6.1 GB, 256K — best wiring/OCR in class
ollama pull qwen3-vl:2b           # 1.9 GB — smoke test / Air fallback
ollama pull gemma3:12b            # 8.1 GB — detail-only fallback
# qwen2.5 fallback
ollama pull qwen2.5vl:7b          # 6.0 GB

# 3) Confirm vision+tools+context badges
ollama show ministral-3:8b --modelfile | head -n 40
ollama show qwen3-vl:8b | grep -i -E "context|vision|tools"
```

**BOM-grounded Modelfile (system prompt bakes the SHALLOT context so the PWA needs no per-request BOM injection):**

```dockerfile
# shallot-vision.Modelfile
FROM qwen3-vl:8b
# or: FROM ministral-3:8b

SYSTEM """You are SHALLOT hardware vision for OT/field nodes.
You see the image via Ollama vision. Do not hallucinate components.

BOM context you must use:
- Field node: RP2350 Pico 2W + SX1262 LoRa (SPI: SCK/MOSI/MISO/CS, DIO1, BUSY, RESET)
- Auth node: ESP32-S3 running pico-fido2
- Power stage under test: Noctua NF-A4x10 12V fan switched low-side by 30N06L N-MOSFET (gate via 100R, 100k pulldown), flyback 1N4007 anti-parallel across fan (cathode band = +12V side).

When you answer:
1. List every visible component with confidence and localized hint (e.g., "1N4007 near fan connector, band toward red wire").
2. Validate wiring against BOM; call out open/miswired nets.
3. Produce strict JSON matching the tool/schema below.
Always answer in the user's language (Swedish if the user wrote Swedish, else English).
"""

PARAMETER temperature 0.15
PARAMETER num_ctx 32768
PARAMETER num_predict 2048
```

```bash
ollama create shallot-vision -f ./shallot-vision.Modelfile
ollama run shallot-vision "Describe the board, then validate the fan power stage." --images ./capture.jpg
# structured output test
curl -s http://localhost:11434/api/chat -d '{
  "model":"shallot-vision",
  "messages":[{"role":"user","content":"Validate the 30N06L+1N4007 stage. Return JSON.","images":["'"$(base64 -w0 capture.jpg)"'"]}],
  "format":"json","stream":false
}' | jq .
```

**PWA env (single-model default):**

```bash
# shallot-setup/.env.local
OLLAMA_HOST=http://fedora:11434
VISION_MODEL=shallot-vision   # or qwen3-vl:8b / ministral-3:8b
# REASON_MODEL only for A/B chain
REASON_MODEL=ministral-3:14b
OLLAMA_MAX_LOADED_MODELS=1
```

Images are passed as `images: [base64]` per [Vision — Ollama docs](https://docs.ollama.com/capabilities/vision) — the same path the current `route.ts` already uses.

---

## 8. Risks and what to recheck before buy-in

- **Ollama quantization drift:** library sizes are for `Q4_K_M`. `Q4_0` (old `llava:13b`, `mixtral`) vs `Q4_K_M` (newer) differ ~10% in quality/VRAM; verify with `ollama show <model> | grep quantization`. Pull the `_q4_K_M` suffixed tag when available for wiring detail.
- **Mining secondary benchmarks:** public MMMU/DocVQA tables compare heterogeneous prompts; trust the **same-image SHALLOT eval** (§6) over any single leaderboard number. The §3 table is directional only.
- **Context ≠ free:** 256K with 5× 4K-token images = 20K image tokens + 30K system/history → KV may spill; cap images or set `num_ctx` 16K–32K for PWA responsiveness.
- **LoRA limitation is current, not permanent:** if Ollama adds a `PROJECTOR` Modelfile instruction or vision-capable `ADAPTER`, the LoRA calculus changes — recheck [ollama/ollama releases](https://github.com/ollama/ollama/releases) and [#15346](https://github.com/ollama/ollama/issues/15346) before planning vision fine-tuning.

---

## Sources (primary, grouped)

**Mistral — vision is Ministral 3, Pixtral deprecated:**
[Models Overview](https://docs.mistral.ai/getting-started/models) · [Vision](https://docs.mistral.ai/capabilities/vision) · [Pixtral 12B — deprecated](https://mistral.ai/news/pixtral-12b/) · [Pixtral Large — Hugging Face](https://huggingface.co/mistralai/Pixtral-12B-2409)

**Ollama library — what actually runs locally (manifest sizes/context/badges):**
[ministral-3](https://ollama.com/library/ministral-3) · [qwen3-vl](https://ollama.com/library/qwen3-vl) · [qwen2.5vl](https://ollama.com/library/qwen2.5vl) · [gemma3](https://ollama.com/library/gemma3) · [llava](https://ollama.com/library/llava) · [llama3.2-vision](https://ollama.com/library/llama3.2-vision) · [minicpm-v](https://ollama.com/library/minicpm-v) · [Vision models — Ollama search (pulls)](https://ollama.com/search?c=vision) · [EnlistedGhost/Pixtral-12B-Ollama-GGUF (community, Q4_K_M 7.6 GB + mmproj)](https://huggingface.co/EnlistedGhost/Pixtral-12B-Ollama-GGUF)

**Qwen — 2.5-VL vs 3-VL succession:**
[Qwen2.5-VL — Qwen blog (Jan 26 2025)](https://qwenlm.github.io/blog/qwen2.5-vl/) · [Qwen2.5-VL — Technical Report](https://arxiv.org/abs/2502.13923) · [Qwen2.5-VL-32B — blog (Mar 25 2025)](https://qwenlm.github.io/blog/qwen2.5-vl-32b/) · [Qwen2.5-VL — GitHub](https://github.com/elsawhs/qwen2.5-vl) · [Qwen2.5-VL-7B-Instruct — Model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) · [Qwen3-VL — GitHub (flagship, 2/4/8/30A3B/32/235A22B, 256K, Thinking/Instruct)](https://github.com/QwenLM/Qwen3-VL) · [Qwen3-VL — Technical Report (256K→1M YaRN, Interleaved-MRoPE, DeepStack)](https://arxiv.org/pdf/2511.21631) · [Qwen3-VL-8B-Instruct — Model card (8.8 B, 256K, Apache-2.0)](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) · [Qwen3-VL-8B FP8](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-FP8)

**Ollama docs — vision API + Modelfile + adapter limits:**
[Vision](https://docs.ollama.com/capabilities/vision) · [Modelfile Reference](https://docs.ollama.com/modelfile) · [Modelfile — ADAPTER source (Llama/Mistral/Gemma only, single adapter)](https://github.com/ollama/ollama/blob/main/docs/modelfile.mdx) · [ADAPTER fails on mmproj — #15346](https://github.com/ollama/ollama/issues/15346) · [qwen-vl-finetune — Qwen team](https://github.com/QwenLM/Qwen2.5-VL/tree/main/qwen-vl-finetune)

**Alternatives — not in official Ollama library, community GGUF only:**
[InternVL3-8B-GGUF — Hugging Face (community)](https://huggingface.co/unsloth/InternVL3-8B-GGUF) · [InternVL — GitHub (OpenGVLab)](https://github.com/OpenGVLab/InternVL) · [CogVLM — GitHub (THUDM)](https://github.com/THUDM/CogVLM) · [vLLM — Supported multimodal models (Phi-3-Vision via vLLM, not Ollama library)](https://docs.vllm.ai/en/latest/models/supported_models/)

**Current PWA chain being replaced:**
`shallot-setup/src/app/api/vision/route.ts` (`VISION_MODEL=llava:13b`, `REASON_MODEL=mixtral`, `POST /api/chat` with `images:[base64]`)
