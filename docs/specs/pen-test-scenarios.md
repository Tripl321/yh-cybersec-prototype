# Specification: SHALLOT Pen-test-scenarier (Pen-Test Scenarios)

**Issue:** [#6](https://github.com/Tripl321/yh-cybersec-prototype/issues/6) (T7 Grilling)  
**Author:** AI Agent & Johannes  
**Date:** 2026-08-13  
**Status:** Resolved (grilled)

---

## 1. Overview

Denna spec definierar pen-test-scenarierna som validerar **Beroende 2 – Säkerhetspostur** i SHALLOT (variabeltabell i kartan #1): i vilken utsträckning SHALLOT mitigerar MITRE ATT&CK **T1078 (Valid Accounts)** jämfört med baseline. Scenarierna bygger direkt på hotmodellen och 3-lagers Defense-in-Depth från [`docs/research/mitre-t1078-picofido.md`](docs/research/mitre-t1078-picofido.md) (#3).

---

## 2. Metod (Q1, hybrid + simulering)

Tre pelare, proportionerliga mot 4 veckors projekt:

1. **Praktiskt** — attacker mot den byggda prototypen där det är genomförbart (RF/presence-vektorer).
2. **Tabletop** — analytisk genomgång av de vektorer som jämförs mot analog baseline.
3. **Simulering** — för kryptografiska vektorer som inte är etiskt/praktiskt testbara fysiskt (visa att origin-bound challenge + nonce-replay misslyckas, utan verklig side-channel).

---

## 3. Testmiljö & avgränsning (Q3)

- **Kontrollerat eget lab** med: 2× Pico 2 W (badge + gateway/"Mama bear"), LoRa SX1262 (Core1262-HF), 1.54" e-ink, LiPo 400 mAh.
- **Ingen koppling till riktigt OT-nätverk.** Prototypen är en **labbdemonstrator**, inte deploybar i produktions-OT. En potentiellt farlig prototyp (experimentell krypto, LoRa, LiPo) förs inte in i en verklig OT-miljö — det vore att bryta mot secure-by-design "fail-safe defaults" och god praxis. Validering sker mot modellen, inte mot levande industri.
- Se hårdvara i [`docs/research/shallot-hardware-architecture-cost.md`](docs/research/shallot-hardware-architecture-cost.md) (#9).

---

## 4. Scenariokatalog (Q2 — alla 8 vektorer)

Varje scenario: metod-klass, förväntat säkert utfall, observation, pass/fail, koppling till kontroll.

| ID | Vektor (från #3) | Metod | Förväntat utfall (mitigation) | Ramverk |
|---|---|---|---|---|
| **S1** | T1078.001 Delade lokala konton | Tabletop (baseline-jämförelse) | SHALLOT: unika kryptografiskt bundna creds/operatör; ingen delad nyckel | NIST IA-2(2), CIS 6.4 |
| **S2** | T1078.004 Default-konton på gateway/PLC | Tabletop | Gateway kräver FIDO2-PIN + UP; default-konto ej möjligt | NIST IA-2(1), CIS 6.3 |
| **S3** | Fysisk nyckel/bricka-kloning (analog T1078) | Tabletop | Privat nyckel extraheras ej (RP2350 Secure Lock/OTP) | NIST IA-5(11) |
| **S4** | Relay / range-extension av Transit-heartbeat | **Praktiskt** (relä med 2× LoRa) eller Simulerad | Replay av nonce-märkt heartbeat misslyckas; session ej etableras utanför närvaro | NIST IA-3(1) |
| **S5** | RF-jamming → fail-safe lock | **Praktiskt** (stör med 2:a SX1262) | Heartbeat-förlust → omedelbar terminal-lock (<3 s) | NIST IA-3(1), CIS 6 |
| **S6** | Flash/hardware-extraction (side-channel) | Simulerad | RP2350 Secure Boot + OTP-skydd; nyckel ej läsbar | NIST IA-5(11) |
| **S7** | Förlorad bricka → credential revocation | **Praktiskt** (revoke via gateway) | Återkallad badge nekas inom sekunder; fallback nyckel | Residual-risk #1 (#3) |
| **S8** | Loggförfalskning | Teoretisk/Simulerad | Varje auth-event krypto-signat; ej förfalskbar | NIST CSF PR.AC-1, CIS 6.5 |

**Testbara på prototyp:** S4, S5, S7. **Teoretiska/Simulerade:** S1, S2, S3, S6, S8.

---

## 5. Framgångskriterier (Q4)

Per scenario: definiera **förväntat säkert utfall** + **observerat resultat** + **bedömning (pass/fail/partial)**.

- Auto-lock vid >2 m: **≤ 3 s** (S5).
- Relay (S4): ingen session etableras utanför avsett avstånd / replay nekas.
- Jamming (S5): omedelbar lock vid heartbeat-förlust (fail-safe default).
- Revocation (S7): badge nekas omedelbart efter återkallelse.
- Krypto-vektorer (S1–S3, S6, S8): argumentation + simulering visar att angreppspotentialen är nära noll.

---

## 6. Leverans (Q5)

- Denna spec (`docs/specs/pen-test-scenarios.md`) som scenariokatalog + resultatmall.
- **Resultatavsnitt i slutrapporten** (Beroende 2): för varje scenario förväntat vs observerat utfall, sammanställt mot MITRE T1078-mappningen från #3.

---

## 7. Etik & säkerhet (Q6)

- **Endast authorized pen-test i eget lab.** Inget intrång i tredjepartssystem, inget test mot verklig OT-infrastruktur.
- Prototypen hanteras som labbdemonstrator (se §3).
- Li-Po enligt säkerhetsrutin (se #5 Q6 / hårdvarurapport).

---

## 8. Koppling till övriga issues

- **#3** MITRE T1078-mappning — källan till scenarierna.
- **#9** Hårdvara — komponenterna som testmiljön byggs av.
- **#5** Användartest-design — Beroende 3 (separat metod).
- **#8** Rapportstruktur — resultatet blir ett avsnitt i slutrapporten.
- **#10** PicoFIDO-integration (blockerad av #8) — praktiska scenarier S4/S5/S7 förutsätter fungerande PicoFIDO-integration.

---

## Next Steps
- **Issue #6 outcome:** Resolved (grilled). Träd: Q1 hybrid+sim · Q2 alla 8 · Q3 eget lab (ej verklig OT) · Q4 pass/fail-kriterier · Q5 spec+rapport · Q6 authorized eget lab.
- Specen matar #8 (rapportstruktur) och de praktiska scenarierna (S4/S5/S7) förutsätter #10 (PicoFIDO-integration).
- **Blockeringsstatus:** #7 och #8 var blockerade av #5,#6 — båda är nu lösta, så #7 och #8 är **avblockerade**.
