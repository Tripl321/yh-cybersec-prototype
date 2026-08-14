# SHALLOT — Hårdvarustatus (Hardware Status)

> Inventering av faktisk hårdvarustatus för SHALLOT-prototypen. Uppdaterad
> 2026-08-13 utifrån ticket [#17](https://github.com/Tripl321/yh-cybersec-prototype/issues/17).
> Syfte: visa vad som är monterat/flashat/testat och vad som blockerar
> firmware- och radio-arbete.

## Sammanfattning
- **FIDO2-autenticatorn är den enda del som faktiskt är verifierad:** en ESP32
  flashad med `pico-fido2` har registrerats mot demo-servern över USB HID.
- **All övrig hårdvara är inköpt men ej påbörjad** (RP2350, LoRa, e-ink, LiPo,
  Arduino UNO Q).
- **Blocker:** hårdvaran är ej monterad/ihopsatt → firmware- och radio-arbete
  kan inte påbörjas förrän komponenterna kopplas upp.

## Avvikelse mot BOM (viktig)
`CONTEXT.md` och ticket #17 antar **RP2350 (Pico 2 W)** som FIDO-plattform.
Den FIDO-enhet som faktiskt validerats är en **ESP32 + pico-fido2**
([polhenarejos/pico-fido2](https://github.com/polhenarejos/pico-fido2)).
pico-fido2 bygger på Pico SDK, så ESP32-bygget/porten bör bekräftas vid
vidare arbete. RP2350-brädorna har ännu ingen tilldelad roll i prototypen.

## Inventeringslista
| Komponent | Antal | Status | Anteckning |
| --- | --- | --- | --- |
| RP2350 (Pico 2 W) | 2 | Inköpt, ej påbörjat | Roll (Mama Bear/Cub?) ej klar |
| RP2350 dev-board | 1 | Inköpt, ej påbörjat | |
| Arduino UNO Q | 1 | Inköpt, ej påbörjat | |
| LoRa SX1262 | 2 | Inköpt, ej påbörjat | Radio / heartbeat över luften |
| e-ink | 1 | Inköpt, ej påbörjat | Display |
| LiPo | 1 | Inköpt, ej påbörjat | Strömförsörjning |
| **ESP32 + pico-fido2** | 1 | **Flashat + registrerat (USB HID)** | AVVIKELSE: BOM antog RP2350 |

## FIDO-enhet — vad som är testat respektive ot testat
**Testat (verifierat):**
- Flaskad med pico-fido2-firmware.
- Registrerad mot `demo/`-servern över USB HID (WebAuthn-RP-flödet fungerar
  med riktig hårdvara).

**Otestat med den verkliga ESP32-enheten:**
- **Attestation:** servern begär nu `DIRECT` (se ADR/PR #24); oklart om
  enheten sänder `packed`/`self`-attestation — måste testas, annars rejectas
  registreringen.
- **User Verification (PIN):** ej testat.
- **Transports:** USB HID verifierat; BLE/NFC saknas i pico-fido2 (se
  forskning #13).
- **Resident/discoverable credentials:** ej testat (servern använder
  `RESIDENT_KEY=PREFERRED`).
- **Fysisk inkapsling** (wood/fanér per NOTES): ej gjord.

## Blockeringar
- **Hårdvara ej monterad** — komponenter (RP2350, LoRa, e-ink, LiPo, UNO Q)
  är inköpta men inte elektriskt anslutna/monterade. Detta blockerar:
  - Firmware-arbete för Mama Bear/Cub-noder (RP2350).
  - Radio/heartbeat-arbete (LoRa SX1262) — se tickets #4 / #15.
- **Rollfördelning (korrigerad):** RP2350 (Pico 2 W) = Mama bear / PicoFIDO (per CONTEXT.md); ESP32+pico-fido2 = testad FIDO-enhet (avvikelse). Cub-agenten är mjukvara som hostas på **Arduino UNO Q eller Fedora** — den stacken är ej spikad (se Cub-agent-ticket).

## Nästa hårdvarusteg
1. Montera/anslut komponenterna (öppna blockeraren ovan).
2. Bekräfta ESP32+pico-fido2-attestation mot DIRECT-kravet (testa registrering
   i webbläsaren mot `localhost:8000`).
3. Tilldela RP2350-brädorna en roll och påbörja firmware.
4. Påbörja LoRa/heartbeat (ticket #15).

Se även [DEVELOPMENT-LOG.md](DEVELOPMENT-LOG.md) och wayfinder-kartan [#11](https://github.com/Tripl321/yh-cybersec-prototype/issues/11).
