# SHALLOT — Utvecklingslogg (Development Log)

> Citerbar sammanställning av vad som byggts och vilka beslut som fattats i
> SHALLOT-prototypen, med länkar till GitHub-issues, PR:er och ADR:er så att
> arbetet kan refereras direkt i uppsatsen.
>
> Senast uppdaterad: 2026-08-19.

## Status just nu
- WebAuthn/FIDO2 auth-server i `demo/` — fungerande och testad (9 tester passerar).
- ADR:er + domänmodell i `docs/adr/`.
- Forskningsrapport (PicoFIDO/CTAP2) i `docs/research/picofido-ctap2-feasibility.md`.
- Attestation-verifiering implementerad (DIRECT som standard, `none` rejectas).
- LoRa radio-lager i `shallot-radio/` — beacon/auth protocol, state machines, relay controller.

## Vad som gjorts (kronologi)
| Steg | Vad | Referens |
| --- | --- | --- |
| 1 | WebAuthn-RP (Flask) med register/login för roller Mama Bear / Cub, SQLite-store, enkelt UI | PR [#22](https://github.com/Tripl321/yh-cybersec-prototype/pull/22) |
| 2 | Mjukvaru-FIDO2-authenticator + end-to-end-test (registrera + logga in) | PR [#22](https://github.com/Tripl321/yh-cybersec-prototype/pull/22) |
| 3 | ADR:er (0001–0003) + domänmodell/ordlista | PR [#21](https://github.com/Tripl321/yh-cybersec-prototype/pull/21) |
| 4 | Forskningsrapport: går PicoFIDO (RP2350) köra CTAP2-passkey? — Ja | Issue [#13](https://github.com/Tripl321/yh-cybersec-prototype/issues/13), PR [#23](https://github.com/Tripl321/yh-cybersec-prototype/pull/23) |
| 5 | Attestation: verifiera self-attestation på hårdvaruvägen, rejecta `none` | Issue [#14](https://github.com/Tripl321/yh-cybersec-prototype/issues/14), PR [#24](https://github.com/Tripl321/yh-cybersec-prototype/pull/24) |
| 6 | LoRa radio-lager: beacon/auth protocol (raw bytes), state machines, relay controller, pin maps | shallot-radio/ |

## Fattade beslut (ADR / tickets)
- **Bibliotek:** `webauthn` (pyauth, v3.x), *inte* `py-webauthn` (felaktigt gammalt paket på PyPI). — [ADR 0001](docs/adr/0001-webauthn-rp-library.md), PR [#21](https://github.com/Tripl321/yh-cybersec-prototype/pull/21)
- **Dev-RP:** localhost:8000 (`host="::"`), `rp.id`/`origin` härleds från `Host`-header; `attestation=none` i ren demo. — [ADR 0002](docs/adr/0002-dev-relying-party-localhost.md), PR [#21](https://github.com/Tripl321/yh-cybersec-prototype/pull/21)
- **Roller:** `mama_bear` (admin/gateway) och `cub` (fältnod/ID-bricka) modelleras som WebAuthn-users med varsin credential-uppsättning. — [ADR 0003](docs/adr/0003-access-roles-mama-bear-cub.md), PR [#21](https://github.com/Tripl321/yh-cybersec-prototype/pull/21)
- **Attestation:** verifiera self-attestation på hårdvaruvägen. Servern begär `DIRECT` som standard och rejectar registreringar där autenticatorn returnerar `fmt=none` (mjukvarunycklar). Enhetsbindning via verifierad attestation (packed/self) + AAGUID. — Issue [#14](https://github.com/Tripl321/yh-cybersec-prototype/issues/14), PR [#24](https://github.com/Tripl321/yh-cybersec-prototype/pull/24)
- **PicoFIDO/CTAP2-feasibility:** genomförbart via `polhenarejos/pico-fido` (USB HID); RP2350 räcker, BLE saknas. — Issue [#13](https://github.com/Tripl321/yh-cybersec-prototype/issues/13), PR [#23](https://github.com/Tripl321/yh-cybersec-prototype/pull/23)
- **Raw bytes for LoRa framing:** struct.pack/unpack, no JSON. — [ADR 0008](docs/adr/0008-raw-bytes-for-lora-framing.md)
- **Epoch context in auth frame:** day field for offline revocation. — [ADR 0009](docs/adr/0009-epoch-context-in-auth-frame.md)

## Hårdvara (validerad)
- ESP32 flashad med `pico-fido2` ([polhenarejos/pico-fido2](https://github.com/polhenarejos/pico-fido2)) har registrerats mot demo-servern över USB HID — WebAuthn-RP-integrationen är validerad med riktig hårdvara. — Issue [#6](https://github.com/Tripl321/yh-cybersec-prototype/issues/6)
- **Avvikelse:** `CONTEXT.md` antog RP2350 Pico 2 W; faktisk testad hårdvara är ESP32. pico-fido2 bygger på Pico SDK, så ESP32-bygget/porten bör bekräftas vid vidare arbete.

## Reproducera / testa
```bash
cd demo
../.venv/bin/python app.py            # webbserver på http://localhost:8000
../.venv/bin/python -m pytest -q     # 9 tester (smoke + e2e)
```
Riktig hårdvara registreras i webbläsaren mot `localhost:8000` (kräver att
autenticatorn sänder packed/self-attestation på DIRECT-vägen).

## Öppna frågor (wayfinder-frontier)
- [#17](https://github.com/Tripl321/yh-cybersec-prototype/issues/17) hårdvarustatus: vad är monterat / otestat
- [#18](https://github.com/Tripl321/yh-cybersec-prototype/issues/18) hur mäts "usable security" i utvärderingen
- [#19](https://github.com/Tripl321/yh-cybersec-prototype/issues/19) rollmodell Mama Bear/Cub → WebAuthn (fördjupning)
- [#12](https://github.com/Tripl321/yh-cybersec-prototype/issues/12) PicoFIDO↔server-integration (blockerad av #17)
- [#4](https://github.com/Tripl321/yh-cybersec-prototype/issues/4) / [#15](https://github.com/Tripl321/yh-cybersec-prototype/issues/15) Heartbeat/Transit-protokoll (blockerat av #17)

Hela kartan: issue [#11](https://github.com/Tripl321/yh-cybersec-prototype/issues/11).

## Vad som INTE är loggat i repot
- Den löpande chattkonversationen (frågor/svar, steg-för-steg-resonemang) finns
  inte i repot — endast beslutens *resultat* (ovan + ADR/ärenden).
- Lokala, ocommittade ändringar i `.agents/skills/*`, `CONTEXT.md`, `README.md`,
  `docs/specs/*` är inte incheckade och ingår inte i ovanstående.
- Auth-servern är en prototyp, inte produktionshärdad (se karta #11, Out of scope).
