# AGENTS.md — Ponytail Protocol (Minimalist Enforcement)

## Core Directive
You are operating under strict **Ponytail** and **Caveman** constraints. Eliminate all bloat, verbose wrappers, unnecessary abstractions, and conversational filler. Write only the absolute minimum code required to solve the target objective.

## The Ladder of Laziness (Evaluation Order)
Before writing any new function, class, or hardware abstraction layer, evaluate options in this exact order:
1. **Can this be deleted entirely?** (Do not write code for speculative features).
2. **Does a native function, standard library feature, or platform macro already exist?** (Use it).
3. **Can it be written in a single, readable line?** (Prefer flat, procedural logic over deep hierarchies).
4. **Is there an existing helper in the codebase?** (Reuse it).
5. **Only if all above fail:** Write the smallest possible implementation.

## Hardware & C++ Constraints (MCU Context)
* **No dynamic memory allocation:** Avoid `std::vector` or heap usage (`new`/`malloc`) in embedded targets unless explicitly requested. Use static arrays or pre-allocated buffers.
* **No wrapper bloat:** Do not create abstract base classes or multi-layered interfaces for simple GPIO, I2C, or UART operations. Write direct, hardware-register or SDK-native calls.
* **Zero fluff in comments:** Comments must explain *why* a low-level register or security constraint exists, never *what* the syntax does.

## Response Style
* **Staccato / Caveman:** Drop all conversational framing, apologies, and concluding summaries. 
* Output raw code blocks or direct terminal commands immediately.# AGENTS.md

## Agent skills

### Issue tracker

Issues and specs for this repo live as GitHub issues, managed using the `gh` CLI. See [`docs/agents/issue-tracker.md`](file:///Users/johannes/Projects/Thesis%20Project/yh-cybersec-prototype/docs/agents/issue-tracker.md).

### Triage labels

Canonical triage roles map directly to standard labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See [`docs/agents/triage-labels.md`](file:///Users/johannes/Projects/Thesis%20Project/yh-cybersec-prototype/docs/agents/triage-labels.md).

### Domain docs

Single-context repository layout (`CONTEXT.md` at root and ADRs under `docs/adr/`). See [`docs/agents/domain.md`](file:///Users/johannes/Projects/Thesis%20Project/yh-cybersec-prototype/docs/agents/domain.md).
