# Research Report: NIST SP 800-63B Usable Security & Design Requirements for SHALLOT

**Issue:** [#2](https://github.com/Tripl321/yh-cybersec-prototype/issues/2) (T2 Research)  
**Author:** AI Agent  
**Date:** 2026-08-13  
**Status:** Completed  

---

## Primary Sources

1. **NIST SP 800-63B**: *Digital Identity Guidelines: Authentication and Lifecycle Management* (Section 10 "Usability Considerations", Section 5 "Authenticator Types", AAL Levels). [NIST SP 800-63B](https://pages.nist.atl.nist.gov/800-63-3/sp800-63b.html)
2. **Ka-Ping Yee (2002)**: *User Interaction Design for Secure Systems*, UC Berkeley / Security and Usability.
3. **Cranor, L. F. (2008)**: *A Framework for Reasoning About the Human in the Loop*, IEEE Security & Privacy.
4. **Sasse, M. A. et al. (2001)**: *Transforming Security from Barrier to Enabler*, UCL.
5. **FIDO Alliance (2023)**: *FIDO UX Guidelines & Passkey Central Design Patterns*. [Passkey Central](https://passkeycentral.org/)

---

## Executive Summary

This research investigates the usable security principles outlined in NIST SP 800-63B Section 10 and foundational academic literature (Ka-Ping Yee, Cranor, Sasse). It translates these principles into five concrete, testable design requirements for the **SHALLOT Smart ID Badge** (PicoFIDO + E-ink + Transit Heartbeat Proximity Verification) in an Operational Technology (OT) lab environment.

---

## 1. NIST SP 800-63B Usability Guidelines Analysis

NIST SP 800-63B explicitly establishes that **usability and security are interdependent**. When authentication mechanisms introduce unnecessary friction, users develop workaround behaviors (e.g., propping doors open, sharing credentials, forging paper logs) that severely degrade the real-world security posture.

### Key Guidelines & Mappings to SHALLOT

1. **Risk-Based Usability (§10.1)**
   - *Guideline:* Usability must be integrated into authentication risk management. Authenticators offering higher assurance (AAL2/AAL3) should be designed to reduce cognitive overhead compared to lower-assurance legacy methods.
   - *SHALLOT Mapping:* Replaces manual paper logging + physical key management (high friction, zero cryptographic assurance) with PicoFIDO (AAL3 hardware passkey) + automated Transit proximity heartbeat.

2. **Phishing Resistance & Cryptographic Origin Binding (§5.1.2, §10.2)**
   - *Guideline:* Systems should shift security burden from human vigilance (detecting AiTM/phishing) to cryptographic protocols (FIDO2/WebAuthn origin binding).
   - *SHALLOT Mapping:* PicoFIDO handles domain-bound cryptographic challenges, eliminating credential theft or social engineering risks for OT operators.

3. **Elimination of Unnecessary User Burden (§10.2, §10.3)**
   - *Guideline:* Eliminate arbitrary periodic password changes, complex memorization rules, and repetitive manual re-authentications.
   - *SHALLOT Mapping:* Operators authenticate once via FIDO2 button press; ongoing proximity is verified passively via encrypted RF heartbeat, removing repetitive password typing in industrial gear.

4. **Clear Feedback & Status Indication (§10.1)**
   - *Guideline:* Systems must provide unambiguous, continuous feedback regarding authentication state, active sessions, and security actions.
   - *SHALLOT Mapping:* An ultra-low-power E-ink display on the Smart ID Badge provides persistent visual confirmation of active access state, identity, and proximity status.

---

## 2. Academic Usable Security Principles

### Principle 1: "Make the Secure Path the Easy Path" (Path of Least Resistance)
*Sources: Ka-Ping Yee (2002), Cranor (2008)*

- **Core Rule:** If the secure workflow requires more physical steps or higher latency than an insecure bypass, users will default to the bypass.
- **SHALLOT Application:** Gaining access to an OT terminal via SHALLOT requires placing the ID-badge within proximity and pressing the PicoFIDO button (1 step, < 2 sec). In contrast, the baseline solution requires locating a physical key, unlocking a door/cabinet, and manually signing a paper logbook (multiple steps, > 15 sec).

### Principle 2: "Visible Security" (Visibility & Transparency)
*Sources: Ka-Ping Yee (2002), Dourish et al. (2004)*

- **Core Rule:** The security state must be visible and self-explanatory without creating visual noise or requiring active status queries.
- **SHALLOT Application:** The E-ink screen displays real-time status:
  - `AUTHENTICATED: ZONE A` (Active access)
  - `OUT OF RANGE: LOCKED` (Heartbeat lost > 3 seconds)
  - `ADMIN MODE: MAMA BEAR` (Privileged mode)

### Principle 3: "Minimal User Burden" (Passive & Continuous Verification)
*Sources: Sasse et al. (2001), NIST SP 800-63B §10.2*

- **Core Rule:** Active user intervention (button press / PIN) should be required only to establish intent at trust boundaries. Session maintenance should be passive.
- **SHALLOT Application:** "Authenticate once with intent (FIDO2 button tap), verify continuously via passive proximity (Transit heartbeat)".

---

## 3. FIDO2 / CTAP 2.2 UX Recommendations

1. **User Presence (UP):** A physical button tap on RP2350 PicoFIDO confirms explicit human presence.
2. **User Verification (UV):** PIN protection on Admin PicoFIDO (#2) ensures two-factor compliance for privileged access (NIST SP 800-53 IA-2(1)).
3. **Explicit Failure Modes:** Distinct visual/auditory signals for:
   - Heartbeat range loss (Out of Range)
   - Invalid credential / unauthorized badge
   - Battery low warning

---

## 4. Concrete Design Requirements for SHALLOT

| ID | Requirement Name | Source | Target Metric / Evaluation Method |
|---|---|---|---|
| **REQ-UX-01** | **Single-Tap Access Intent** | FIDO Alliance UX, Yee (Path of Least Resistance) | ≤ 1 physical interaction (PicoFIDO button tap) to authenticate |
| **REQ-UX-02** | **Passive Proximity Maintenance** | Sasse (2001), NIST SP 800-63B §10.2 | Continuous encrypted RF heartbeat; zero manual re-authentications while in range |
| **REQ-UX-03** | **Persistent Zero-Power Display** | Yee (Visibility), NIST §10.1 | E-ink screen updates status within < 500 ms and retains display at 0 mW idle power |
| **REQ-UX-04** | **Immediate Range Lockout** | NIST SP 800-53 IA-3(1), CIS Control 6 | Auto-lock terminal within ≤ 3 seconds of heartbeat loss (> 2 meters range) |
| **REQ-UX-05** | **Role-Based Token Isolation** | NIST SP 800-53 IA-2(1)/(2) | Separate physical tokens for Field Operator (Pico #1) vs Admin Mama Bear (Pico #2) |

---

## Conclusion & Next Steps for Issue #2

This research establishes the theoretical and regulatory foundation for SHALLOT's usable security architecture. 

- **Issue #2 Outcome:** Resolved and documented.
- **Unblocks:** [#4 (Issue #5 in GitHub: T5 Grilling - Usable security-heuristik-val)](https://github.com/Tripl321/yh-cybersec-prototype/issues/4).
