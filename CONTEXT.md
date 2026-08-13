# CONTEXT.md — yh-cybersec-prototype

## Domän

OT-säkerhet (Operational Technology) — åtkomstkontroll för industriella miljöer.

## Nyckelbegrepp

- **SHALLOT** — Proximity-baserat säkerhetssystem för OT-åtkomst
- **Smart ID-bricka** — Secure-by-design ID-bricka med PicoFIDO + E-ink + heartbeat
- **PicoFIDO** — FIDO2-passkey på Raspberry Pi Pico 2 W (RP2350)
- **Mama bear** — Admin/gateway-åtkomstpunkt, separat PicoFIDO
- **Heartbeat** — Krypterad proximity-verifiering mellan ID-bricka och fältnod
- **Transit** — SHALLOT:s krypterade heartbeat-protokoll
- **Baseline** — Fysisk nyckel + pappersloggbok (analog åtkomst)
- **Secure by design** — Minsta privilegium, defense in depth, fail-safe defaults

## Ramverk

- NIST CSF 2.0, NIST SP 800-53r5, MITRE ATT&CK, CIS Controls v8
- PicoFIDO: FIDO2/CTAP 2.2, WebAuthn

## Hårdvara

- 2× Raspberry Pi Pico 2 W (RP2350) — fält + admin PicoFIDO
- E-ink-skärm, LiPo-batteri, RFM69HW-radio (kandidat)
- Inkapsling: wood/fanér
- Budget: 4000 SEK
