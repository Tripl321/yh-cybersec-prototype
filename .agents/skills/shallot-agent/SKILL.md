---
name: shallot-agent
description: Drive the SHALLOT OT-security prototype from task to verified demo. Use for SHALLOT planning, GitHub/Craft tracking, PAW, FIDO Key, Field Node, Mama Bear, LoRa/SX1262, RP2350, PicoFIDO, firmware, hardware assembly, bring-up, security tests, thesis evidence, or project-status questions.
---

# SHALLOT Agent

Deliver the smallest verified step toward the physical end-to-end demo.

## Load truth

1. Read `AGENTS.md`.
2. Read `CONTEXT.md`; use its vocabulary.
3. Read relevant accepted ADRs and the narrowest applicable spec.
4. Inspect current code, tests, hardware material, Git state, and linked issue before acting.

Precedence for conflicts:

1. Physical measurements and manufacturer datasheets
2. `CONTEXT.md` and accepted ADRs
3. Current code and tests
4. Current GitHub issue/spec
5. Craft tracker/build guide
6. Historical status documents

Surface conflicts. Never silently merge incompatible architectures.

## Fixed architecture

```text
Mama Bear --USB provisioning--> PAW / Field Node
FIDO Key --USB-serial signing--> PAW
Field Node --Beacon over LoRa--> PAW
PAW --Auth request over LoRa--> Field Node --relay--> OT device
```

- PAW: Feather RP2350 + E-ink + Core1262-HF + LiPo.
- FIDO Key: ESP32-S3-Nano running PicoFIDO.
- Field Node: Pico 2 W + Core1262-HF + relay.
- Mama Bear: Arduino UNO Q; air-gapped provisioning root. No LoRa, fan, or MOSFET.

## Route work

### Planning and status

- GitHub Issues are canonical.
- Craft is the operational mirror.
- Craft task collection: `284301a9-d31b-376c-6069-a82ed3587e8e`.
- Craft tracker document: `bc215539-8f0f-f6c9-1fbf-72e00a6e24a4`.
- Reconcile both before claiming status.
- End with one concrete next action and its verification criterion.

### Hardware

1. Identify exact board/module revision from markings or photos.
2. Verify pinout, voltage, current, polarity, and connector orientation against manufacturer material.
3. Produce a wire table: source pin, destination pin, signal, expected idle voltage.
4. Power from current-limited USB first. Add LiPo only after USB bring-up.
5. Check resistance to ground before power; measure rails before inserting the radio.
6. Attach a matched 868 MHz antenna before SX1262 transmission.
7. Bring up one interface at a time: power → SPI → radio standby → RX/TX → peripherals.
8. Record measurements and move the Craft task to `Verifiering`; use `Klar` only after evidence.

Unknown pinout or logic level means `Blockerad`, not a guessed wire.

### Firmware and code

- Follow `AGENTS.md` and existing seams.
- Preserve fixed-width raw-byte LoRa framing.
- Preserve fail-closed behavior: relay OFF on boot, timeout, weak RSSI, invalid signature, replay, or expired epoch.
- Keep hardware I/O behind the existing callbacks only where already established.
- Run the narrowest changed tests, then the relevant suite.
- Hardware-dependent behavior requires bench evidence; mocks alone are insufficient.

### Security verification

Test at minimum:

- valid auth grants access;
- invalid HMAC rejects;
- reused nonce/counter rejects;
- expired epoch rejects;
- RSSI below threshold rejects;
- heartbeat timeout returns relay OFF;
- reboot starts relay OFF;
- provisioning commands are ignored outside physical provisioning mode.

Capture command, result, timestamp, hardware revision, firmware revision, and measured latency/RSSI where applicable.

## Tracking transitions

- `Backlog`: scoped, not ready.
- `Nästa`: unblocked and actionable.
- `Pågår`: physical or code work started.
- `Blockerad`: missing evidence, component, decision, or dependency.
- `Verifiering`: implementation complete; acceptance evidence pending.
- `Klar`: acceptance criterion observed and recorded.

When work changes scope or behavior, update the GitHub issue first, then Craft. Never create a second source of truth.

## Completion

A task is complete only when:

- requested artifact or physical step exists;
- applicable tests/checks passed;
- fail-closed behavior remains intact;
- GitHub and Craft reflect reality;
- evidence and remaining limitation are stated.
