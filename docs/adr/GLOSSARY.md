# SHALLOT — domänmodell / ordlista

Ubiquitous language för SHALLOT-prototypen. Kombinerar OT-domänen (från `CONTEXT.md`) med WebAuthn/FIDO2-begreppen som `demo/`-servern introducerar.

## OT-domän (SHALLOT)

- **SHALLOT** — Presence-baserat säkerhetssystem för OT-åtkomstkontroll. I komponentledet även benämning på själva ID-brickan (FIDO2-hårdvaran).
- **Smart ID-bricka / PicoFIDO** — Secure-by-design ID-bricka; FIDO2-passkey (hårdvara: ESP32-S3-nano med `pico-fido2`-firmware, validerad mot demo-servern).
- **Mama Bear** — Admin/gateway-åtkomstpunkt (separat PicoFIDO). Roll: `mama_bear`.
- **Cub** — LLM-baserad AI-agent (Pydantic AI + lokal Ollama) som hostas på Fedora. Hanterar GRC, SIEM-auditering, loggkontroll och larm inom SHALLOT. Roll: `cub` (WebAuthn-user).
- **Heartbeat** — Krypterad närvaroverifiering (presence) mellan ID-bricka och fältnod; bekräftar att brickan är kvar, inte dess avstånd (SX1262 mäter inte distans; äkta distans = UWB secure ranging).
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

## AI-agent / stack (Cub)

- **Pydantic AI** — Lean, typ-säker agent-ramverk (Python); modell-agnostiskt.
- **Ollama** — Lokal LLM-runtime (Fedora); kör modeller utan egress/API-nyckel.
- **Model-agnostic** — Provider-abstraktion; byter Ollama ↔ moln utan kodändring.
- **Tool-allowlist** — Explicit lista av verktyg modellen får anropa per kontext; begränsar blast radius.
- **SOAR** — Security Orchestration, Automation and Response; Cub agerar SOAR-likt för larm inom SHALLOT.
- **Prompt-injection** — Attack där olitlig text (t.ex. loggar) försöker styra agenten; motverkas genom data/instruktions-isolering.
- **Sandbox (Podman)** — Rootless container, drop caps, read-only rootfs, seccomp, nätverk låst till provider.

## Mappning OT → WebAuthn

| SHALLOT / Smart ID-bricka | FIDO2-hårdvaran (autenticatorn) — motsvarar credentialt som lagras för user `cub` |
| --- | --- |
| Mama bear | user med roll `mama_bear` + credentials (admin/gateway) |
| Cub (agent) | user med roll `cub` + credential; LLM-agent (Pydantic AI + lokal Ollama) hostad på Fedora |
| Presence-åtkomst | (framtida) heartbeat/Transit mellan ID-bricka och fältnod styr auktorisation |
