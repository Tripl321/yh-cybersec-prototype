# 0008 — Raw bytes for LoRa framing

All LoRa communication uses `struct.pack()` / `struct.unpack()` with little-endian byte order. No JSON, no text parsing.

## Why

- **Size**: Beacon is 13 bytes, auth is 41 bytes. JSON would be 80-120 bytes. On LoRa at SF7/125kHz, every byte costs airtime.
- **Reliability**: No parser to fail. No encoding mismatches between CircuitPython on RP2350 and MicroPython on Pico 2 W.
- **Security**: No string injection, no encoding tricks. Fixed-width fields are easier to validate.

## Consequences

- All firmware must share the same format constants (`BEACON_FMT`, `AUTH_FMT`).
- Debugging requires hex dump tools, not plain text.
- Adding new message types means defining a new format string and updating `ShallotRadio.receive()`.
