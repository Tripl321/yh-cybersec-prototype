# Specification: Usable Security Heuristics Framework & Evaluation Protocol

**Issue:** [#4](https://github.com/Tripl321/yh-cybersec-prototype/issues/4) (T5 Grilling)  
**Author:** AI Agent & Johannes  
**Date:** 2026-08-13  
**Status:** Approved / Resolved  

---

## 1. Overview

This document specifies the Usable Security Heuristics Framework and evaluation protocol used to conduct heuristic evaluations of both the **Analog Baseline** (physical key + paper logbook) and the **SHALLOT Smart ID Badge** (PicoFIDO + E-ink + Transit RF heartbeat).

---

## 2. Theoretical Framework

The framework combines:
1. **Ka-Ping Yee's Principles of Secure Interaction Design** (2002)
2. **NIST SP 800-63B Section 10 Usability Guidelines** (2020)
3. **Nielsen's 0–4 Severity Rating Scale** (1994)

---

## 3. The 8 Usable Security Heuristics Matrix

Each solution (Baseline vs. SHALLOT) is evaluated against these 8 criteria:

| ID | Heuristic Name | Description / Requirement | Primary Source |
|---|---|---|---|
| **H1** | **Path of Least Resistance** | The secure method must be the easiest, fastest, and lowest-effort path for the operator compared to any bypass. | Ka-Ping Yee (2002), Cranor (2008) |
| **H2** | **Visibility of Security State** | System lock status, active role, and authentication state must be immediately visible without active user queries. | Ka-Ping Yee (2002), NIST SP 800-63B §10.1 |
| **H3** | **Minimal User Burden** | Session maintenance requires zero repetitive manual re-authentications or complex password memorization. | Sasse (2001), NIST SP 800-63B §10.2 |
| **H4** | **Explicit Intent & Authorization** | Initiating access requires explicit, unambiguous user intent (e.g. FIDO2 button tap) confirming human presence. | FIDO Alliance UX, Ka-Ping Yee (2002) |
| **H5** | **Unambiguous Failure States** | System errors, out-of-range events, and access rejections are self-explanatory with actionable guidance. | NIST SP 800-63B §10.1 |
| **H6** | **Immediate Lockout & Revocation** | System automatically revokes access / locks terminal upon boundary or proximity violation (< 3 sec). | NIST SP 800-53 IA-3(1), CIS Control 6 |
| **H7** | **Role & Privilege Isolation** | Standard operator and administrator roles are physically/logically separated to prevent accidental misuse. | NIST SP 800-53 IA-2(1)/(2) |
| **H8** | **Effortless Auditability** | Audit logs and traceability are generated automatically with zero administrative burden on the operator. | NIST CSF PR.AC-1, CIS Control 6 |

---

## 4. Severity Rating Scale (Nielsen 0–4)

During heuristic review, any identified usability problem or flaw is assigned a severity rating:

- **0 - No Problem:** Does not affect usability or security.
- **1 - Cosmetic Problem:** Minor visual/textual issue; fix only if extra time permits.
- **2 - Minor Usability Problem:** Low priority; causes slight delay or confusion but work can proceed.
- **3 - Major Usability Problem:** High priority; causes significant operator friction or potential security workaround. Must be fixed before user testing.
- **4 - Usability Catastrophe:** Critical defect; prevents secure operation or forces security bypass. Mandatory fix.

---

## 5. Evaluation Protocol

1. **Evaluators:** Expert heuristic review conducted prior to human user testing ([#5](https://github.com/Tripl321/yh-cybersec-prototype/issues/5) - T6).
2. **Procedure:** Both the Analog Baseline workflow and SHALLOT prototype workflow are walked through step-by-step against H1–H8.
3. **Output:** A comparative heuristic evaluation table with severity ratings and recommendations.
