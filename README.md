# yh-cybersec-prototype — SHALLOT

**Secure-by-design OT-åtkomstkontroll med phishing-resistent FIDO2-hårdvara.**

> YH-projekt (cybersecurity). Målet med projektet är att demonstrera modern,
> människonära säkerhet i en OT-miljö — och att visa upp den kompetensen för
> framtida arbetsgivare inom OT-säkerhet / identitets- och åtkomsthantering (IAM).

---

## Varför detta projekt

Industriella miljöer (OT) skyddas ofta fortfarande av fysiska nycklar och
pappersloggböcker — en "baseline" som är opålitlig och omöjlig att revisera.
Behovet är **phishing-resistent åtkomstkontroll** som håller även om operatören
luktas på en nätfiskelänk.

SHALLOT svarar med en *secure-by-design* lösning: en ID-bricka (FIDO2/
WebAuthn) som bevisar identitet kryptografiskt, kombinerat med
proximity-verifiering (heartbeat) mellan bricka och fältnod.

**Vad projektet bevisar för en arbetsgivare:** jag kan designa och bygga en
funktionande säkerhetskontroll med *riktig hårdvara*, inte en mock — och jag
kan förankra den i erkända ramverk och dokumentera varje beslut.

---

## Vad projektet visar (skills → anställning)

| Kompetens | Hur det visas här |
| --- | --- |
| **Phishing-resistent auth** (FIDO2 / CTAP 2.2 / WebAuthn) | Relying Party byggd & testad mot verklig hårdvara (ESP32 + pico-fido2), registrerad över USB HID |
| **Secure by design** (least privilege, defense in depth, fail-safe) | Varje arkitekturbeslut fångat som ADR i `docs/adr/` |
| **Ramverk** (NIST CSF 2.0, SP 800-53r5, MITRE ATT&CK, CIS Controls v8) | Genomsyrar designen (se `CONTEXT.md`) |
| **Fullstack-säkerhet** | Python/Flask-RP, krypto (ECDSA/DER), CTAP-attestation & -assertion, SQLite |
| **Hårdvarunära säkerhet** | Flashning av FIDO2-firmware, USB HID, egen RP som verifierar enhet |
| **Användbar säkerhet** (usable security) | Planerad utvärdering — se ticket #18 |
| **Dokumentation & beslutslogg** | Citerbar utvecklingslogg (`docs/DEVELOPMENT-LOG.md`) för rapporten |

---

## Arkitektur (kort)

- **SHALLOT / Smart ID-bricka** — FIDO2-hårdvaran (autenticatorn).
- **Cub** — agenten (mjukvara, Python på Fedora) som agerar mot brickan.
- **Mama bear** — admin / gateway-åtkomstpunkt.

```
[ID-bricka / SHALLOT] ──(FIDO2 / USB HID)──> [Cub-agent] ──> [Mama bear / gateway]
                                    │
                          (heartbeat / Transit över LoRa — planerat)
```

---

## Demo — körbar på ett par kommandon

```bash
cd demo
python -m venv .venv && . .venv/bin/activate
pip install flask webauthn cryptography cbor2 pytest
../.venv/bin/python app.py          # webbserver på http://localhost:8000
```

Sedan registrera en passkey i webbläsaren (roll `mama_bear` eller `cub`) och
logga in. Med riktig hårdvara (ESP32 + pico-fido2) registreras brickan mot
servern över USB HID.

```bash
../.venv/bin/python -m pytest -q   # 9 tester (smoke + end-to-end)
```

**Säkerhetsdetalj:** servern begär `DIRECT` attestation och rejectar
mjukvarunycklar (`fmt=none`) när attestation krävs — credentialt bindas till
en verifierad enhet.

---

## Repo-struktur

| Sökväg | Innehåll |
| --- | --- |
| `demo/` | WebAuthn auth-server (Flask) + mjukvaru-authenticator + tester |
| `docs/adr/` | ADR 0001–0004 + domänmodell (GLOSSARY) |
| `docs/HARDWARE-STATUS.md` | Inventering av faktisk hårdvara |
| `docs/DEVELOPMENT-LOG.md` | Citerbar utvecklingslogg (referens för rapporten) |
| `docs/research/picofido-ctap2-feasibility.md` | Forskning: PicoFIDO/CTAP2 |
| `CONTEXT.md` | Domän, ramverk, hårdvara |

---

## Status

**Klart:** auth-server (register/login, roller), attestation-verifiering,
validering mot riktig FIDO2-hårdvara, ADR:er, rollmodell, Cub-stack (Fedora/Python).

**Pågår / planerat:** Cub-agent (Python), Heartbeat/Transit över LoRa,
utvärdering av usable security (#18), fysisk inkapsling.

---

## Teknik

Python · Flask · `webauthn` (FIDO2/CTAP 2.2/WebAuthn) · `cryptography` · `cbor2` ·
SQLite · ESP32 / pico-fido2 · (planerat) LoRa SX1262.
