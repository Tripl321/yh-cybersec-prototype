# SHALLOT concept map (wayfinder)

> Local-markdown tracker (`gh` unauthenticated; public API used for read-only
> issue lookup). Map is the canonical artifact. One session plans; execution
> hand-resolves nothing.

## Destination

`docs/SHALLOT-concept.md` — a complete, self-consistent concept specification
for SHALLOT without LoRa. Covers all components (PAW, FIDO Key, DEN/Field
Node, Mama Bear), the communication model, key lifecycle, security
properties, and fail-closed behaviour. Done when the spec is complete and
self-consistent.

## Notes

- Domain: OT security, proximity-based access control (SHALLOT)
- Skills: domain-modeling, grilling, shallot-agent, writing-for-agents
- CONTEXT.md vocabulary governs, with one correction: **DEN (Decision
  Enforcement Node) = Field Node**. Use both, DEN when precise.
- AGENTS.md Ponytail/Caveman constraints apply (minimal, no bloat)
- LoRa is OUT OF SCOPE — no radio beacon / auth frame / heartbeat tickets
- Active implementation source of truth:
  `hardware/contact-auth/` (merged to `main`)
- Budget: 4000 SEK | 4 weeks MVP (CONTEXT.md)
- Local Ollama + qwen3-vl:8b available for harness work, not needed here

## Decisions so far

- [Hardware BOM delta without LoRa modules](HARDWARE-STATUS.md#inventeringslista) — LoRa SX1262 ×2 removed. BOM: RP2350 (Pico 2 W) ×2, RP2350 dev-board ×1, Arduino UNO Q ×1, e-ink ×1, LiPo ×1, ESP32+pico-fido2 ×1. No new hardware needed.
- [Comms topology without LoRa](https://github.com/Tripl321/yh-cybersec-prototype/issues/97) — **docked UART between PAW and DEN** (Serial1 @115200, pogo-pins/USB-C). Physical docking is the proximity proof. LoRa is legacy/target, not active transport. Sources: `hardware/contact-auth/docs/11-dockat-uart-protokoll.md`, `docs/architecture-pivot-2026-09-09.md`.
- [PAW role](../hardware/contact-auth/docs/11-dockat-uart-protokoll.md) — **responder only**. Never initiates. Answers `CHALLENGE(8B nonce)` with `RESPONSE(32B HMAC-SHA256)`, may send `ALARM(1B)` and answer `HEARTBEAT(0B)`. 3 AUTHENTICATED/DENIED display only as abstract icons, no PII. FIDO Key is not in the link path.
- [DEN (Field Node) role](../hardware/contact-auth/docs/13-pro-53-fail-closed.md) — **initiator and sole decision authority**. `DENIED → CHALLENGE_SENT → AUTHENTICATED → DENIED`. 2 s response deadline, 100 ms byte timeout, 1 s session gap. Every error → DENIED. Checks HMAC, then Ed25519-signed blocklist, then relay/ACK. ACK is informational only.
- [Mama Bear provisioning](../hardware/contact-auth/docs/14-provisioning-v2-design.md) — air-gapped trust root. Provisioning v2: PAW Ed25519 identity + X25519 ephemeral + HKDF-SHA256 + AES-128-GCM wrapped operations key. MPU/Bridge see public fields only; raw keys never leave MCU/PAW SRAM.
- [FIDO Key scope](../hardware/contact-auth/docs/19-fido2-designspec.md) — **separate identity track**, not PAW–DEN link auth. FIDO2/CTAP2 at ESP32-S3 (Pico Fido) covers user/admin identity and presence; UART/HMAC covers badge authenticity.
- [Security properties without radio](../hardware/contact-auth/docs/07-sakerhetsdesign.md + `13`) — no RSSI gating. Proximity = physical dock. Replay rejected by fresh 64-bit TRNG nonce + 2 s deadline. Constant-time HMAC compare. CRC32 framing. Volatile SRAM keys; power loss = key loss = deny.

## Not yet specified (fog)

- How a FIDO2 admin approval becomes authoritative for provisioning/blocklist issuance (doc 19 §9 next step: Mama Bear countersignature) — concept-level open point, not blocking a first spec.
- Whether the LoRa TX-only alarm channel returns later (explicitly out of scope now).

## Out of scope

- LoRa SX1262 radio, beacon, auth frame, heartbeat, OTA alarm channel (user decision 2026-10-25; doc 00-scope agrees)
- Pogo-dock mechanical design (implementation task PRO-85, not a concept decision)
- Multi-PAW / multi-site deployment
- Formal security proof, pen-test execution, production hardening

## Tickets

| Ticket (question) | Type | Blocked by | Status |
|---|---|---|---|
| Comms topology without LoRa | research | — | resolved |
| PAW role without LoRa beacon/auth | research | Comms topology | resolved |
| DEN (Field Node) role without LoRa | research | Comms topology | resolved |
| Hardware BOM delta without LoRa modules | task (AFK) | — | resolved |
| Mama Bear provisioning fit | research | Comms topology | resolved |
| FIDO Key integration without LoRa frame | research | Comms topology | resolved |

**Frontier: empty.** The way to `docs/SHALLOT-concept.md` is clear — no
decisions remained before writing it.

Destination reached 2026-10-25: `docs/SHALLOT-concept.md` written on branch
`docs/shallot-concept` (draft v1.0). Map closed; remaining work is review and
commit/PR, not another wayfinding session.
