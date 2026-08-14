# SHALLOT — domänmodell / ordlista

Ubiquitous language för SHALLOT-prototypen. Kombinerar OT-domänen (från `CONTEXT.md`) med WebAuthn/FIDO2-begreppen som `demo/`-servern introducerar.

## OT-domän (SHALLOT)

- **SHALLOT** — Proximity-baserat säkerhetssystem för OT-åtkomstkontroll. I komponentledet även benämning på själva ID-brickan (FIDO2-hårdvaran).
- **Smart ID-bricka / PicoFIDO** — Secure-by-design ID-bricka; FIDO2-passkey (hårdvara: RP2350 Pico 2 W, i praktiken även ESP32 med `pico-fido2`-firmware).
- **Mama Bear** — Admin/gateway-åtkomstpunkt (separat PicoFIDO). Roll: `mama_bear`.
- **Cub** — Agent (mjukvara) som hostas på Arduino UNO Q eller Fedora. Roll: `cub` (WebAuthn-user).
- **Heartbeat** — Krypterad proximity-verifiering mellan ID-bricka och fältnod.
- **Transit** — SHALLOT:s krypterade heartbeat-protokoll (ännu ej designerat, se karta #4/#15).
- **Baseline** — Fysisk nyckel + pappersloggbok (analog åtkomst, fallback).

## WebAuthn / FIDO2 (demo/-servern)

- **Relying Party (RP)** — Servern (`demo/app.py`) som begär och verifierar attestation/assertion.
- **rp.id** — Relying Party-identifieraren; måste vara suffix av browserns ursprung. I demo härledd från `Host`.
- **User / Credential** — En registrerad användare (med roll) och dess nyckelpar. Lagras i `demo/db.py` (SQLite).
- **Challenge** — Engångs-nonce som servern genererar och verifierar för att stoppa replay.
- **Attestation** — Tillverkares intyg om autenticatorns ursprung. Demo kör `none` (ingen verifiering).
- **Registration** — `navigator.credentials.create` → `verify_registration_response`; lagrar credential.
- **Authentication / Assertion** — `navigator.credentials.get` → `verify_authentication_response`; loggar in.
- **User Verification (UV)** — Autenticatorn verifierar användaren (PIN/biometri). Demo kräver inte UV.

## Mappning OT → WebAuthn

| SHALLOT / Smart ID-bricka | FIDO2-hårdvaran (autenticatorn) — motsvarar credentialt som lagras för user `cub` |
| --- | --- |
| Mama bear | user med roll `mama_bear` + credentials (admin/gateway) |
| Cub (agent) | user med roll `cub` + credential; agenten hostas på UNO Q eller Fedora |
| Proximity-åtkomst | (framtida) heartbeat/Transit mellan ID-bricka och fältnod styr auktorisation |
