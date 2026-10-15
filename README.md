# yh-cybersec-prototype — SHALLOT

**Secure-by-design OT-åtkomstkontroll med phishing-resistent FIDO2-hårdvara.**

> Detta är det kanoniska SHALLOT-repositoryt. Den tidigare separata
> contact-auth-implementationen migreras till `hardware/contact-auth/`; se ADR
> 0012 och modulens `MIGRATION.md`.

> YH-projekt (cybersecurity). Målet med projektet är att demonstrera modern,
> människonära säkerhet i en OT-miljö — och att visa upp den kompetensen för
> framtida arbetsgivare inom OT-säkerhet / identitets- och åtkomsthantering (IAM).

---

## Varför detta projekt

Industriella miljöer (OT) skyddas ofta fortfarande av fysiska nycklar och
pappersloggböcker — en "baseline" som är opålitlig och omöjlig att revisera.
Behovet är **phishing-resistent åtkomstkontroll** som håller även om operatören
luras av en nätfiskelänk.

SHALLOT svarar med en *secure-by-design* lösning: en ID-bricka (FIDO2/
WebAuthn) som bevisar identitet kryptografiskt, kombinerat med
närvaroverifiering mellan bricka och fältnod.

**Vad projektet bevisar för en arbetsgivare:** jag kan designa och bygga en
fungerande säkerhetskontroll med riktig hårdvara och förankra den i erkända
ramverk med dokumenterade beslut.

---

## Vad projektet visar (skills → anställning)

| Kompetens | Hur det visas här |
| --- | --- |
| **Phishing-resistent auth** | FIDO2/CTAP 2.2/WebAuthn och verifierad hårdvara |
| **Fail-closed hårdvaruautentisering** | PAW–DEN UART challenge-response under `hardware/contact-auth/` |
| **Secure by design** | Arkitekturbeslut i `docs/adr/` |
| **Ramverk** | NIST CSF 2.0, SP 800-53r5, MITRE ATT&CK och CIS Controls v8 |
| **Fullstack-säkerhet** | Python, Flask, kryptografi, SQLite och agentplattform |
| **Hårdvarunära säkerhet** | RP2350, ESP32, UART, LoRa, USB HID och e-Paper |
| **Användbar säkerhet** | Planerad utvärdering, se ticket #18 |

---

## Arkitektur (kort)

- **PAW** — Feather RP2350, e-Paper och autentiseringsfirmware.
- **DEN / Field Node** — Pico 2/RP2350 som fattar fail-closed åtkomstbeslut.
- **FIDO Key** — ESP32-S3-Nano med PicoFIDO.
- **Mama Bear** — lokal admin- och provisioneringsnod.

Den aktiva hårdvaru-MVP:n använder dockad UART mellan PAW och DEN. LoRa är
målarkitektur och sekundärt transportspår för bland annat närvaro, larm och
framtida funktioner. Transportvalet får inte beskrivas som färdigverifierat utan
att aktuell modul och dokumentation anges.

---

## Demo

```bash
cd demo
python -m venv .venv && . .venv/bin/activate
pip install flask webauthn cryptography cbor2 pytest
../.venv/bin/python app.py
```

```bash
../.venv/bin/python -m pytest -q
```

---

## Repo-struktur

| Sökväg | Innehåll |
| --- | --- |
| `hardware/contact-auth/` | PAW, DEN, Mama Bear, UART-protokoll, CLI och hårdvarutester |
| `demo/` | WebAuthn auth-server och tester |
| `shallot-radio/` | LoRa-protokoll, state machines och relay controller |
| `cub/` | Lokal agent, säkerhetsgrindar och integrationer |
| `ansible/` | Lokal, fail-closed labbautomation |
| `shallot-infra/` | Digestlåst containerreferens och runtimepolicy |
| `docs/adr/` | Arkitekturbeslut och domänmodell |
| `docs/HARDWARE-STATUS.md` | Inventering av faktisk hårdvara |
| `docs/DEVELOPMENT-LOG.md` | Citerbar utvecklingslogg |
| `CONTEXT.md` | Domän, ramverk och hårdvara |

---

## Status

**Klart:** WebAuthn-baseline, FIDO2-attestation, hårdvarunära UART-MVP,
fail-closed PAW–DEN-tester, ADR:er, rollmodell och lokal Cub-stack.

**Pågår:** konsolidering av contact-auth, PRO-45 testdrift, rootless Quadlet,
backup/restore och fysisk verifiering av återstående säkerhetskontroller.

---

## Teknik

Python · Flask · WebAuthn/FIDO2/CTAP 2.2 · HMAC-SHA256 · Ed25519 · SQLite ·
RP2350 · ESP32 · UART · LoRa SX1262 · rootless Podman · Ansible
