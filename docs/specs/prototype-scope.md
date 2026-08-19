# SHALLOT — Prototype Scope

> Defines what ships in the YH thesis demo. Updated after grilling session
> on #16 (OT-access-flöde) and #7 (prototyp-omfattning).

## Demo scenario

**Scenario-based narrative:**

1. Operator approaches field node with ESP32 ID-bricka (PicoFIDO)
2. Badge authenticates via USB HID to field node (RP2350)
3. Field node sends LoRa heartbeat to mama bear (UNO Q gateway)
4. Mama bear forwards to cub-agent on Fedora (live inference via Ollama)
5. Cub-agent processes: scrub → route → egress verify → return decision
6. API returns decision to simulated OT device (laptop)
7. Laptop shows "Access granted → door unlocks" or "Access denied"

**What this proves:**
- Phishing-resistant auth (FIDO2/WebAuthn via PicoFIDO)
- Presence verification (crypto-authenticated heartbeat over LoRa)
- Secure-by-design (cub-agent pipeline: scrubbing, routing, HITL, GRC logging)

## Hardware setup

| Role | Device | Status |
|------|--------|--------|
| ID-bricka (badge) | ESP32-S3-nano + pico-fido2 | ✅ Flashad, validerad |
| Field node | RP2350 dev-board (Qwiic + LiPo) | 🟡 Inköpt, ej påbörjat |
| Mama bear (gateway) | Arduino UNO Q | 🟡 Inköpt, ej påbörjat |
| LoRa radio | 2× Core1262-HF (SX1262, 868 MHz) | 🟡 Inköpt, ej påbörjat |
| Simulated OT device | Laptop (web UI) | ✅ Demo server klar |
| Cub-agent inference | Fedora laptop (Python + Ollama) | ✅ Prototyper klara |

**Connectivity:**
```
[ESP32 Badge] ──(USB HID)──> [RP2350 Field Node]
                                    │
                              (LoRa 868 MHz)
                                    │
                              [UNO Q Mama Bear]
                                    │
                              (USB/Serial)
                                    │
                              [Fedora: Cub-agent]
                                    │
                              (API/HTTP)
                                    │
                              [Laptop: OT Device UI]
```

## Feature status

| Feature | Status | Reference |
|---------|--------|-----------|
| WebAuthn auth-server (Flask) | ✅ Done | demo/ |
| Attestation verification (DIRECT) | ✅ Done | PR #24 |
| PicoFIDO validation (USB HID) | ✅ Done | HARDWARE-STATUS.md |
| Cub-agent scaffold | ✅ Done | PR #51 |
| Ingress scrubber (FPE/hash) | ✅ Done (prototype) | PR #52 |
| Model Router / PDP | ✅ Done (design) | PR #52 |
| Inference Gateway | ✅ Done (design) | PR #53 |
| Local generalization (Tier 1→2) | ✅ Done (prototype) | PR #52 |
| Egress verification | ✅ Done (prototype) | PR #53 |
| FIDO/CTAP tools | ✅ Done (prototype) | PR #54 |
| GRC/SIEM logging | ✅ Done (prototype) | PR #55 |
| Usable security simulation | ✅ Done | PR #56 |
| HITL + provenans-logg | ✅ Done | PR #57 |
| LoRa radio layer | ✅ Done | shallot-radio/ |
| Field node firmware | 🟡 State machine + relay done, stubs for crypto | shallot-radio/ |
| Mama bear firmware | 🔴 Not started | — |
| Physical enclosure | 🟡 Parts available | #47 |
| Simulated OT device UI | 🔴 Not started | — |
| Cub-agent live integration | 🔴 Not started | — |

## Budget

| Item | Status | Cost |
|------|--------|------|
| Hardware procurement | ✅ Done | 2 541.90 SEK |
| Wood/veneer enclosure | 🟡 Parts available | ~0 SEK |
| Remaining budget | — | ~1 458 SEK (contingency) |
| **Total spent** | — | **2 541.90 SEK of 4 000 SEK** |

## Thesis claims → demo mapping

| Claim | How it's proven | Status |
|-------|----------------|--------|
| Phishing-resistant auth (FIDO2) | ESP32 PicoFIDO registers/authenticates against server | ✅ Validated |
| Presence verification (heartbeat) | LoRa heartbeat between badge and field node | 🟡 Hardware ready, firmware needed |
| Secure-by-design | Cub-agent pipeline (scrub, route, egress verify, HITL, GRC) | ✅ Prototyped, live integration needed |
| NIST CSF / MITRE ATT&CK alignment | ADRs + GRC tools (Sigma, ATT&CK mapping) | ✅ Documented |
| Usable security evaluation | SUS + think-aloud simulation | ✅ Pilot done (#45) |

## Out of scope

- BLE transport (pico-fido2 doesn't support it)
- UWB secure ranging (separate research, out of budget)
- Multi-site deployment
- Formal pen-test execution (scenarios documented in `docs/specs/pen-test-scenarios.md`)
- Formal security proof
- Production hardening of web server
- CI/CD deployment
- Second badge (only 1 badge built)

## Report structure (YH examensarbete)

**Course:** Cybersäkerhet projektarbete (20 YH-poäng, 4 weeks full-time)
**Examination:** Slutrapport + muntlig presentation/demonstration + reflektion
**Grading:** IG / G / VG — VG requires deepened analysis, independence, quality

### Proposed structure (~30 pages)

| Section | Content | ~Pages | Course goal mapping |
|---------|---------|--------|---------------------|
| **1. Sammanfattning** | Executive summary (Swedish + English abstract) | 1 | Kommunicera resultat |
| **2. Introduktion** | Problem statement, thesis claims, SHALLOT overview, avgränsningar | 3 | Analysera problem |
| **3. Bakgrund** | OT security landscape, FIDO2/WebAuthn, threat model (NIST CSF, MITRE ATT&CK, CIS Controls) | 4 | Kunskapsområden |
| **4. Metod** | Project planning (4 weeks), design methodology (ADR), framework alignment, metodval | 2 | Planera projekt |
| **5. Utveckling** | Auth-server, cub-agent stack, PicoFIDO validation, hardware architecture, LoRa heartbeat | 8 | Genomföra projekt |
| **6. Demonstration** | Full pipeline demo (scenario-based), results, usable-security pilot (SUS + think-aloud) | 4 | Kommunicera resultat |
| **7. Diskussion** | Analysis, limitations, related work, future work | 4 | Analysera problem |
| **8. Slutsats** | Conclusions mapped to thesis claims | 2 | — |
| **9. Reflektion** | Learning, career development (OT security / IAM), process reflection | 2 | Yrkesprofilering |
| **Bilagor** | ADRs, code samples, hardware photos, SUS results, pen-test scenarios | — | — |
| | **Total** | **~30 pages** | |

### Section details

**1. Sammanfattning**
- 1 page, Swedish + English
- Problem, method, key results, conclusions
- Keywords: FIDO2, WebAuthn, OT-säkerhet, phishing-resistent, presence verification

**2. Introduktion**
- Problematisering: varför behövs phishing-resistent åtkomstkontroll i OT?
- Thesis claims: (1) phishing-resistant auth, (2) presence verification, (3) secure-by-design
- Avgränsningar: what's in/out of scope (see §Out of scope)
- Disposition: chapter overview

**3. Bakgrund**
- OT security landscape: ICS/SCADA, Purdue model, air-gap myth
- FIDO2/WebAuthn: architecture, CTAP 2.2, attestation
- Threat model: MITRE ATT&CK T1078 (valid accounts), phishing, lateral movement
- Frameworks: NIST CSF 2.0 (Identify, Protect, Detect), NIST SP 800-53r5 (AC-2, IA-2), CIS Controls v8
- Related work: existing OT access control solutions

**4. Metod**
- Project planning: 4-week timeline, milestones, risk management
- Design methodology: ADR (Architecture Decision Records), why ADR over traditional design docs
- Framework alignment: how NIST/ATT&CK/CIS guide design decisions
- Metodval: why FIDO2, why LoRa, why Pydantic AI + Ollama

**5. Utveckling** (longest section — this is where the technical work is documented)
- 5.1 WebAuthn auth-server (Flask): register/login flow, attestation verification, role model
- 5.2 Cub-agent architecture: scaffold, Pydantic AI + Ollama + Podman
- 5.3 Ingress scrubbing: FPE/hash, sensitivity classification, GDPR
- 5.4 Model Router / PDP: tier routing, capability matching, default-deny
- 5.5 Inference Gateway: protocol, policy enforcement, orchestration
- 5.6 Egress verification: capture buffer, deny rules, injection testing
- 5.7 FIDO/CTAP tools: hardware integration, mock backend, HITL gate
- 5.8 GRC/SIEM logging: OTEL, Sigma, ATT&CK mapping, control tags
- 5.9 HITL + provenans: forcing function, rubber-stamp detection, event logging
- 5.10 Hardware architecture: ESP32 PicoFIDO, RP2350 field node, UNO Q gateway, LoRa SX1262

**6. Demonstration**
- 6.1 Demo scenario: step-by-step narrative (badge → field node → mama bear → cub-agent → OT device)
- 6.2 Results: what worked, what didn't, performance metrics
- 6.3 Usable-security pilot: SUS score (72), think-aloud findings, limitations
- 6.4 Security analysis: how the demo proves the thesis claims

**7. Diskussion**
- 7.1 Analysis: what the results mean for OT security
- 7.2 Limitations: hardware constraints, single-badge testing, simulated OT device
- 7.3 Related work: comparison with existing solutions
- 7.4 Future work: BLE, UWB, multi-site, production hardening

**8. Slutsatz**
- Conclusions mapped to each thesis claim
- What was achieved vs what was planned
- Contribution to OT security / IAM field

**9. Reflektion** (course requirement)
- Learning: what skills were developed (FIDO2, cryptography, Python, hardware)
- Career development: how this strengthens OT security / IAM profile
- Process: what went well, what could be improved, project management reflections

### Examination checklist

- [ ] Report follows proposed structure
- [ ] All thesis claims are addressed in §6 (Demonstration) and §8 (Slutsats)
- [ ] ADRs are referenced in §5 (Utveckling) and §7 (Diskussion)
- [ ] Hardware photos included in §5.10 or Bilagor
- [ ] SUS results included in §6.3
- [ ] Pen-test scenarios referenced in §7.2 (Limitations)
- [ ] Reflektion section addresses all three course competencies (independence, collaboration, career profiling)
- [ ] Presentation demonstrates the full pipeline (live or recorded)
- [ ] References follow consistent citation style
