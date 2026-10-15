# SHALLOT contact-auth hardware module

> Canonical location: `hardware/contact-auth/` in
> `Tripl321/yh-cybersec-prototype`. This module was selectively migrated from
> `yh-contact-auth-projektarbete`; see [MIGRATION.md](MIGRATION.md).

This module contains the active hardware-focused SHALLOT MVP for authentication
between a Personal Access Wearable (**PAW**) and a Decision Enforcement Node
(**DEN**).

The current bench MVP uses physical USB-C docking and UART communication. LoRa
remains as legacy, test, and future transport material, including OTA and a
one-way alarm channel, but it is not the primary active authentication
transport in this module.

## Security

Authentication uses challenge-response with:

- HMAC-SHA256
- nonces against replay
- fail-closed state transitions
- CRC-protected framing

Key generation and provisioning are handled by **Mama Bear**. Historical code
and documents may still use the name UNO Q.

## Hardware

- **DEN** — Raspberry Pi Pico 2/RP2350 with Core1262
- **PAW** — Adafruit Feather RP2350 with Core1262 and Waveshare e-Paper
- **Mama Bear** — key generation and provisioning authority

## Structure

```text
plc/                DEN firmware and legacy LoRa/key tracks
id-kort/            PAW firmware, e-Paper, and hardware tests
key-authority/      Mama Bear and historical UNO Q components
shared/             Shared UART protocol
libraries/          DenUartProtocol and Ed25519 support
 tools/shallot_cli/ Local test, simulation, and diagnostics CLI
 tests/             Protocol, security, and integration tests
 docs/              Requirements, architecture, protocol, and security design
```

## Verification

Create an isolated local environment and run the migration baseline:

```fish
python -m venv .venv
source .venv/bin/activate.fish
python -m pip install -e '.[test]'
python tools/check_pytest_baseline.py
```

The baseline currently permits only the two documented PRO-45 failures in
[MIGRATION.md](MIGRATION.md). It performs no hardware access unless an explicit
CLI hardware command is separately invoked.
