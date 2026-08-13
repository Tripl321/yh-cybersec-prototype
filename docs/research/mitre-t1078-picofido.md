# Research Report: MITRE ATT&CK T1078 Mitigation & Framework Mapping for PicoFIDO + SHALLOT

**Issue:** [#3](https://github.com/Tripl321/yh-cybersec-prototype/issues/3) (T3 Research)  
**Author:** AI Agent  
**Date:** 2026-08-13  
**Status:** Completed  

---

## Primary Sources & Standards

1. **MITRE ATT&CK Framework**: Technique [T1078 (Valid Accounts)](https://attack.mitre.org/techniques/T1078/) & Sub-techniques (T1078.001 Local, T1078.002 Domain, T1078.003 Cloud, T1078.004 Default Accounts). Mitigation M1032 (Multi-factor Authentication).
2. **NIST SP 800-53 Rev 5**: Security Controls catalog — Identification & Authentication (IA) Family:
   - `IA-2(1)` MFA for Privileged Accounts
   - `IA-2(2)` MFA for Non-Privileged Accounts
   - `IA-3(1)` Cryptographic Bidirectional Device Authentication
   - `IA-5(11)` Hardware Token-based Authentication
   - `AC-2` Account Management & `AC-7` Unsuccessful Logon Attempts
3. **NIST CSF 2.0**: Protect (PR) Function — PR.AA (Authentication & Access Control), PR.AC-1, PR.AC-2, PR.AC-7.
4. **CIS Controls v8**: Control 6 (Access Control Management) — Sub-controls 6.3, 6.4, 6.5.
5. **PicoFIDO (RP2350) Architecture**: FIDO2 / CTAP 2.2 specification, RP2350 OTP & Secure Boot / Secure Lock.

---

## Executive Summary

This report maps the threat vectors associated with **MITRE ATT&CK T1078 (Valid Accounts)** in an OT/ICS environment and demonstrates how **PicoFIDO (RP2350 FIDO2 passkey)** combined with **SHALLOT (Transit RF Heartbeat Proximity + E-ink)** systematically mitigates these vectors. It provides a formal mapping to NIST SP 800-53 Rev 5, NIST CSF 2.0, and CIS Controls v8, contrasting the posture against the analog baseline.

---

## 1. Threat Analysis: MITRE ATT&CK T1078 (Valid Accounts) in OT

Adversaries exploiting T1078 use legitimate credentials to log in, bypass detection mechanisms, and move laterally across OT networks.

### Specific T1078 Attack Vectors in OT:
1. **T1078.001 (Local Accounts):** Shared operator credentials on local HMIs / field terminals.
2. **T1078.004 (Default Accounts):** Unchanged factory credentials on industrial gateways/PLCs.
3. **Physical Key & Badge Cloning (Analog T1078 equivalent):** Impersonating authorized personnel by duplicating a physical key or forging a paper logbook entry.
4. **Relay & Proximity Spoofing:** Relaying an active session signal across unauthorized distances.

---

## 2. Mitigation via PicoFIDO + SHALLOT Architecture

SHALLOT mitigates T1078 through a 3-layer Defense-in-Depth model:

```
[Layer 1: FIDO2 Hardware Token]  -->  Cryptographic Origin Binding (PicoFIDO RP2350)
[Layer 2: Proximity Heartbeat]   -->  Encrypted Transit RF Heartbeat (Passive Auto-Lock)
[Layer 3: Role & Device Isolation]-->  Pico #1 (Field / IA-2(2)) vs Pico #2 (Admin / IA-2(1))
```

### Attack Mitigation Comparison: Baseline vs. PicoFIDO + SHALLOT

| Attack / Threat Vector | Baseline (Physical Key + Paper Log) | PicoFIDO + SHALLOT | Mitigation Mechanism |
|---|---|---|---|
| **Credential Harvesting / Phishing (T1078)** | N/A (Analog) | **Mitigated (Near Zero)** | FIDO2 origin-bound public key cryptography; no shared secret transmitted. |
| **Physical Key Duplication / Impressioning** | **High Risk** | **Mitigated (Zero)** | RP2350 Secure Lock + OTP key storage prevents extraction of private keys. |
| **Log Forgery / Unattributable Access** | **High Risk** (Paper logs editable/fakeable) | **Mitigated (High Integrity)** | FIDO2 audit logs + cryptographic signature per auth event. |
| **Unauthorized Session Persistence (Abandonment)** | **High Risk** (Terminal left unlocked) | **Mitigated (Auto-Lock < 3s)** | Transit RF heartbeat locks HMI immediately when operator steps > 2m away. |
| **Relay / Range Extension Attack** | N/A | **Mitigated (Heartbeat Cryptography)** | Nonce-based bidirectional RF challenge-response (IA-3(1)). |
| **Flash Memory Extraction / Hardware Side-Channel** | N/A | **Mitigated (Hardware Security)** | RP2350 Hardware Isolation, OTP memory protection & Secure Boot. |

---

## 3. Standards & Framework Mapping

### A. NIST SP 800-53 Rev 5 Mapping

- **IA-2(1) MFA for Privileged Accounts:** Fully satisfied by Admin PicoFIDO (#2, "Mama bear") requiring FIDO2 PIN + User Presence button tap.
- **IA-2(2) MFA for Non-Privileged Accounts:** Fully satisfied by Field PicoFIDO (#1) for field operators.
- **IA-3(1) Cryptographic Bidirectional Device Authentication:** Satisfied by SHALLOT Transit RF encrypted heartbeat between Smart Badge and Field Node.
- **IA-5(11) Hardware Token-Based Authentication:** Satisfied by RP2350 hardware-bound cryptographic keys.
- **AC-2 & AC-7 Account Management & Unsuccessful Attempts:** PicoFIDO rate-limits PIN attempts to prevent brute-force attacks.

### B. NIST CSF 2.0 Mapping

- **PR.AA-01 (Identity & Credentials Managed):** Cryptographic FIDO2 credentials bound to hardware tokens.
- **PR.AA-03 (MFA Implemented):** Hardware-based MFA for all access points.
- **PR.AA-05 (Access Rights Managed):** Strict separation between Field (Pico #1) and Admin (Pico #2).

### C. CIS Controls v8 Mapping

- **CIS 6.3 (Require MFA for Dedicated Administrative Accounts):** Enforced by Admin PicoFIDO (#2).
- **CIS 6.4 (Require MFA for Remote/Field Access):** Enforced by Field PicoFIDO (#1) + Transit Heartbeat.
- **CIS 6.5 (Centralize Access Control):** Verifiable digital audit trail for every authentication event.

---

## 4. Residual Risks & Technical Countermeasures

| Residual Risk | Severity | Countermeasure in SHALLOT |
|---|---|---|
| **Single Point of Failure (Lost Badge)** | Medium | Rapid credential revocation via Gateway API + physical key fallback |
| **RF Jamming / Interference** | Low/Medium | Fail-safe default: Heartbeat loss causes immediate terminal lock |
| **Physical Theft of Token** | Low | FIDO2 PIN protection (User Verification) prevents unauthorized use |

---

## Conclusion & Next Steps for Issue #3

- **Issue #3 Outcome:** Resolved and documented.
- **Unblocks:** [#6 (T7 Grilling: Pen-test-scenarier)](https://github.com/Tripl321/yh-cybersec-prototype/issues/6) and [#10 (T11 Grilling: PicoFIDO-integration med SHALLOT)](https://github.com/Tripl321/yh-cybersec-prototype/issues/10).
