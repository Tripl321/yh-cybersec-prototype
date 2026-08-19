# GRC Control Registry — SHALLOT

Central mapping of all security/compliance controls across 5 frameworks to
concrete code components, ADRs, and implementation status. Used by cub-agent's
`grc_siem.py` for automated compliance checks and by the installer for
compliance visualization.

**Frameworks:** NIST CSF 2.0 · NIST SP 800-53r5 · MITRE ATT&CK · CIS Controls v8 · EU AI Act

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented in code |
| 🔧 | Partially implemented / prototype |
| 📋 | Designed in ADR, not yet coded |
| ❌ | Gap identified, planned |

## Control → Component Matrix

### 1. Access Control (AC)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | PR.AA-01 | `cub/tools/fido_ctap.py` — FIDO2 hardware auth | ADR 0007 | ✅ |
| NIST CSF 2.0 | PR.AA-03 | `cub/tools/hanko_client.py` — WebAuthn RP | ADR 0007 | ✅ |
| NIST CSF 2.0 | PR.AA-05 | `cub/hitl/__init__.py` — operator confirmation gates | ADR 0006 | ✅ |
| SP 800-53 | AC-2 Account Management | `cub/tools/hanko_client.py` — user lifecycle | ADR 0007 | ✅ |
| SP 800-53 | AC-3 Access Enforcement | `cub/router/__init__.py` — PDP policy routing | ADR 0006 | ✅ |
| SP 800-53 | AC-4 Information Flow | `cub/router/__init__.py` — sensitivity → tier routing | ADR 0006 | ✅ |
| SP 800-53 | AC-6 Least Privilege | `cub/tools/__init__.py` — explicit tool-allowlist | ADR 0005 | ✅ |
| SP 800-53 | AC-7 Unsuccessful Login | `cub/tools/hanko_client.py` — Hanko manages lockout | ADR 0007 | 🔧 |
| CIS v8 | 6.1 Inventory of Auth | `cub/tools/hanko_client.py` — passkey registry | ADR 0007 | ✅ |
| CIS v8 | 6.2 centralized auth | `cub/tools/hanko_client.py` — Hanko central auth | ADR 0007 | ✅ |
| MITRE | T1621 MFA Request | `cub/tools/fido_ctap.py` — FIDO2 challenge-response | ADR 0007 | ✅ |
| MITRE | T1078 Valid Accounts | `cub/router/__init__.py` — default-deny routing | ADR 0006 | ✅ |
| EU AI Act | Art. 9 Risk Mgmt | `cub/router/__init__.py` — policy prevents unsafe tiers | ADR 0006 | ✅ |

### 2. Data Protection (DP)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | PR.DS-01 | `cub/scrubber/__init__.py` — AES-SIV encryption | ADR 0006/0007 | ✅ |
| NIST CSF 2.0 | PR.DS-10 | `cub/scrubber/__init__.py` — entity surrogate encoding | ADR 0006 | ✅ |
| NIST CSF 2.0 | PR.DS-11 | `cub/memory/__init__.py` — encrypted at rest | ADR 0007 | ✅ |
| SP 800-53 | SC-8 Transmission Conf. | `cub/egress/__init__.py` — deny-by-default + TLS | ADR 0006 | ✅ |
| SP 800-53 | SC-28 Protection at Rest | `cub/scrubber/__init__.py` — AES-SIV | ADR 0006/0007 | ✅ |
| SP 800-53 | SC-7 Boundary Protection | `cub/egress/__init__.py` — Podman deny-by-default | ADR 0005/0006 | ✅ |
| CIS v8 | 3.11 Encrypt Portable | `cub/scrubber/__init__.py` — scrub before any output | ADR 0006 | ✅ |
| CIS v8 | 13.1 Secure Network Arch | `cub/egress/__init__.py` — localhost-only egress | ADR 0005 | ✅ |
| MITRE | T1048 Exfil Alt Protocol | `cub/egress/__init__.py` — URL/pattern blocking | ADR 0006 | ✅ |
| MITRE | T1530 Cloud Storage Data | `cub/memory/__init__.py` — local-first, scrubbed writes | ADR 0007 | ✅ |
| EU AI Act | Art. 10 Data Quality | `cub/scrubber/__init__.py` — scrub training/RAG inputs | ADR 0006 | ✅ |
| GDPR | Art. 5(1)(c) Minimization | `cub/scrubber/__init__.py` — entity minimization | ADR 0006/0007 | ✅ |
| GDPR | Art. 25 Privacy by Design | `cub/memory/__init__.py` — TTL/purge, local-first | ADR 0007 | ✅ |

### 3. Detection & Monitoring (DM)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | DE.CM-01 | `cub/tools/grc_siem.py` — Wazuh SIEM events | ADR 0007 | ✅ |
| NIST CSF 2.0 | DE.CM-09 | `cub/egress/__init__.py` — continuous egress monitor | ADR 0006 | ✅ |
| NIST CSF 2.0 | DE.AE-02 | `cub/tools/grc_siem.py` — alert triage + ATT&CK mapping | ADR 0007 | ✅ |
| SP 800-53 | AU-2 Audit Events | `cub/tools/grc_siem.py` — structured GrcEvent schema | ADR 0007 | ✅ |
| SP 800-53 | AU-3 Audit Content | `cub/tools/grc_siem.py` — provenance_id, hash, tier | ADR 0006/0007 | ✅ |
| SP 800-53 | AU-6 Audit Review | `cub/tools/grc_siem.py` — query_events by tag/actor | ADR 0007 | ✅ |
| CIS v8 | 8.1 Audit Log Mgmt | `cub/tools/grc_siem.py` — Wazuh + JSONL fallback | ADR 0007 | ✅ |
| CIS v8 | 8.2 Audit Log Mgmt | `cub/tools/grc_siem.py` — centralized event storage | ADR 0007 | ✅ |
| MITRE | T1041 Exfil Over C2 | `cub/egress/__init__.py` — outbound URL blocking | ADR 0006 | ✅ |
| MITRE | T1562 Impair Defenses | `cub/egress/__init__.py` — injection test corpus | ADR 0006 | ✅ |
| EU AI Act | Art. 12 Logging | `cub/hitl/__init__.py` — provenance log per decision | ADR 0006 | ✅ |
| EU AI Act | Art. 12 Record-Keeping | `cub/tools/grc_siem.py` — Wazuh retention policies | ADR 0007 | 🔧 |

### 4. Human Oversight (HO)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | RS.RP-01 | `cub/hitl/__init__.py` — consequence-based gate | ADR 0006 | ✅ |
| NIST CSF 2.0 | DE.AE-06 | `cub/hitl/__init__.py` — rubber-stamp detection | ADR 0006 | ✅ |
| SP 800-53 | AC-4 Info Flow (human) | `cub/hitl/__init__.py` — high-risk requires operator | ADR 0006 | ✅ |
| CIS v8 | 8.1 Human review | `cub/hitl/__init__.py` — forced human gate for restricted | ADR 0006 | ✅ |
| MITRE | T1566 Phishing (social) | `cub/hitl/__init__.py` — HITL breaks social eng. chain | ADR 0006 | ✅ |
| EU AI Act | Art. 14 Human Oversight | `cub/hitl/__init__.py` — approve/reject/override | ADR 0006 | ✅ |
| EU AI Act | Art. 14(4)(a) Ability to Intervene | `cub/hitl/__init__.py` — operator override | ADR 0006 | ✅ |
| EU AI Act | Art. 14(4)(b) Override | `cub/hitl/__init__.py` — override with logging | ADR 0006 | ✅ |

### 5. Governance & Documentation (GD)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | GV.OC-01 | `docs/adr/` — all ADRs | — | ✅ |
| NIST CSF 2.0 | GV.OC-04 | `CONTEXT.md` — domain glossary | — | ✅ |
| NIST CSF 2.0 | GV.RM-01 | `docs/grc/REGISTRY.md` — this document | — | ✅ |
| SP 800-53 | PL-2 System Plan | `docs/adr/0005-0007` — architecture decisions | — | ✅ |
| SP 800-53 | PM-9 Risk Mgmt Strategy | `cub/router/__init__.py` — deterministic policy | ADR 0006 | ✅ |
| CIS v8 | 1.1 CIS Controls Mgmt | `docs/grc/REGISTRY.md` — this registry | — | ✅ |
| EU AI Act | Art. 9 Risk Mgmt | `cub/router/__init__.py` — default-deny + tier forcing | ADR 0006 | ✅ |
| EU AI Act | Art. 11 Technical Docs | `docs/adr/` + `CONTEXT.md` | — | ✅ |
| EU AI Act | Art. 12 Record-Keeping | `cub/hitl/__init__.py` + `cub/tools/grc_siem.py` | ADR 0006/0007 | ✅ |

### 6. Incident Response (IR)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | RS.MA-01 | `cub/tools/grc_siem.py` — triage_alarm | ADR 0007 | ✅ |
| NIST CSF 2.0 | RS.AN-03 | `cub/tools/grc_siem.py` — forensic query_events | ADR 0007 | ✅ |
| SP 800-53 | IR-4 Incident Handling | `cub/tools/grc_siem.py` — structured alert triage | ADR 0007 | 🔧 |
| CIS v8 | 17.1 Incident Response Plan | `cub/tools/grc_siem.py` + Wazuh playbooks | ADR 0007 | 🔧 |
| MITRE | T1078 Valid Accounts | `cub/tools/grc_siem.py` — ATT&CK technique tagging | ADR 0007 | ✅ |
| MITRE | T1005 Local Data | `cub/scrubber/__init__.py` — scrub before model sees data | ADR 0006 | ✅ |

### 7. Supply Chain & Infrastructure (SC)

| Framework | Control | Component | ADR | Status |
|-----------|---------|-----------|-----|--------|
| NIST CSF 2.0 | ID.SC-01 | `cub/pyproject.toml` — pinned dependencies | — | ✅ |
| NIST CSF 2.0 | PR.IP-12 | ADRs — decisions recorded with rationale | — | ✅ |
| SP 800-53 | SA-12 Supply Chain | `cub/pyproject.toml` — all OSS (MIT/AGPL/Apache) | ADR 0007 | ✅ |
| SP 800-53 | CM-2 Baseline Config | `shallot-infra/compose.yml` — Podman containers | ADR 0005/0007 | 📋 |
| CIS v8 | 2.1 Inventory of Assets | `CONTEXT.md` — hardware inventory | — | ✅ |
| CIS v8 | 15.1 Service Provider Mgmt | ADR 0007 — all components are OSS/self-hosted | ADR 0007 | ✅ |
| NIS2 | Art. 21(2)(f) Supply Chain | `cub/pyproject.toml` — verified OSS stack | ADR 0007 | ✅ |
| CRA | Art. 6 Security by Design | `cub/` — defense-in-depth architecture | ADR 0005/0006 | ✅ |

## Coverage Summary

| Framework | Total Controls | Implemented ✅ | Partial 🔧 | Designed 📋 | Gap ❌ |
|-----------|---------------|---------------|------------|-------------|-------|
| NIST CSF 2.0 | 14 | 13 | 1 | 0 | 0 |
| NIST SP 800-53r5 | 16 | 14 | 2 | 0 | 0 |
| MITRE ATT&CK | 8 | 8 | 0 | 0 | 0 |
| CIS Controls v8 | 10 | 9 | 1 | 0 | 0 |
| EU AI Act | 8 | 7 | 1 | 0 | 0 |
| GDPR | 3 | 3 | 0 | 0 | 0 |
| NIS2 | 1 | 1 | 0 | 0 | 0 |
| CRA | 1 | 1 | 0 | 0 | 0 |
| **Total** | **61** | **56** | **5** | **0** | **0** |

## Key Gaps (Partial Items)

1. **AC-7 Unsuccessful Login** (`hanko_client.py`) — Hanko handles lockout but not explicitly coded in cub-agent; relies on Hanko platform.
2. **Art. 12 Record-Keeping** (`grc_siem.py`) — Wazuh retention policies not yet configured in compose.yml.
3. **IR-4 Incident Handling** (`grc_siem.py`) — triage is coded but automated response playbooks not yet wired.
4. **CM-2 Baseline Config** — `shallot-infra/compose.yml` planned but not yet created.
5. **Art. 12 Logging granularity** — Wazuh log retention/compression rules not configured.

## Component → ADR Traceability

| Code Component | Primary ADR | Secondary ADR | Function |
|----------------|-------------|---------------|----------|
| `cub/router/__init__.py` | ADR 0006 | ADR 0005 | Model routing / PDP |
| `cub/scrubber/__init__.py` | ADR 0006 | ADR 0007 | Ingress scrubbing |
| `cub/hitl/__init__.py` | ADR 0006 | — | Human oversight |
| `cub/egress/__init__.py` | ADR 0006 | ADR 0005 | Egress verification |
| `cub/gateway/__init__.py` | ADR 0006 | ADR 0007 | Inference gateway |
| `cub/tools/grc_siem.py` | ADR 0007 | ADR 0006 | SIEM / GRC events |
| `cub/tools/hanko_client.py` | ADR 0007 | ADR 0001/0002 | WebAuthn RP |
| `cub/tools/fido_ctap.py` | ADR 0007 | ADR 0005 | FIDO2 hardware driver |
| `cub/memory/__init__.py` | ADR 0007 | ADR 0006 | Persistent memory |
| `cub/config/__init__.py` | ADR 0005 | ADR 0006 | Runtime configuration |
| `cub/tools/__init__.py` | ADR 0005 | — | Tool allowlist |
| `cub/__main__.py` | ADR 0007 | ADR 0005 | Entry point + Latitude |

## Usage

- **cub-agent** reads `framework_tags` from events and maps to this registry for compliance queries.
- **Installer** visualizes compliance coverage in the wizard UI (step 4).
- **Wazuh** uses Sigma rules aligned with the MITRE ATT&CK tags in this registry.
- **Thesis documentation** references this registry for the compliance chapter.
