# Spec: SHALLOT Firmware Integration — Making the Prototype Functional

## Problem Statement

The LoRa radio layer, state machines, and relay controller are built (`shallot-radio/`). But the entry points (`fieldnode_main.py`, `paw_main.py`) use stubs for FIDO Key signing, signature verification, E-ink display, and button handling. The prototype cannot run end-to-end without real implementations of these interfaces. Mama Bear provisioning (ENROLL/REVOKE over serial) is not started.

The gap: we have a working radio protocol and state machine, but no way to actually sign, verify, display, or provision.

## Solution

Complete the firmware by implementing the remaining interfaces: FIDO Key USB-serial bridge, E-ink display, button handling, Mama Bear provisioning, and real HMAC verification. Then run end-to-end integration on the lab bench.

## User Stories

1. As a Field Node, I want to verify a badge's HMAC signature against an enrolled key, so that only authorized badges can trigger the relay.
2. As a Field Node, I want to check that the badge's day index is within its valid_until horizon, so that revoked badges are rejected without network access.
3. As a Field Node, I want to track a monotonic counter per badge, so that replayed heartbeats are rejected.
4. As a Field Node, I want to reject heartbeats older than the grace period (5s), so that stale or delayed messages are treated as fail-closed.
5. As a Field Node, I want to store enrolled keys in flash (badge_id → pubkey + epoch_secret + valid_until), so that provisioning survives power cycles.
6. As a Field Node, I want to enter provisioning mode only when a GPIO pin is held low, so that ENROLL is only accepted during physical setup.
7. As a Field Node, I want to parse ENROLL and REVOKE commands over USB-serial, so that Mama Bear can provision and revoke badges.
8. As a Field Node, I want to reply OK/error over serial after ENROLL/REVOKE, so that Mama Bear knows the command succeeded.
9. As a PAW, I want to send (nonce, day) to the FIDO Key over USB-serial and receive a 32-byte HMAC-SHA256 signature, so that I can sign auth requests without holding the private key.
10. As a PAW, I want the FIDO Key to return the signature within 500ms, so that the button-press-to-unlock flow feels instant.
11. As a PAW, I want to detect a button press via hardware interrupt, so that auth is triggered by intentional human action.
12. As a PAW, I want to update the E-ink display on state transitions, so that the worker sees current status (off-site, on-site, granted, denied).
13. As a PAW, I want the E-ink to show credentials + node_id when on-site, so that the worker knows which machine they're near.
14. As a PAW, I want the E-ink to clear (or show generic branding) when off-site, so that shoulder surfing is prevented.
15. As a PAW, I want to receive the current day index from Mama Bear during provisioning, so that epoch signing uses the correct day.
16. As a PAW, I want to store the epoch_secret and valid_until in flash, so that provisioning survives power cycles.
17. As Mama Bear, I want to send ENROLL over USB-serial to a Field Node in provisioning mode, so that a badge's public key is enrolled.
18. As Mama Bear, I want to send REVOKE over USB-serial to a Field Node, so that a badge is immediately denied.
19. As Mama Bear, I want to send epoch_secret + valid_until to a PAW during provisioning, so that the PAW can sign heartbeats with the correct epoch.
20. As Mama Bear, I want to detect whether a connected device is a PAW or Field Node, so that the correct provisioning command is sent.
21. As a developer, I want to run the full flow on a lab bench (PAW button → FIDO Key sign → LoRa → Field Node verify → relay), so that the prototype is demonstrable.
22. As a developer, I want to test ENROLL/REVOKE over serial, so that provisioning is verified.
23. As a developer, I want to test fail-closed behavior (timeout, bad sig, expired epoch), so that the security properties are validated.
24. As a developer, I want to log all access decisions to a file, so that the audit trail is demonstrable.
25. As a developer, I want to flash the firmware to real hardware (Feather RP2350, Pico 2 W, ESP32-S3-Nano), so that the prototype runs on the actual devices.

## Implementation Decisions

### Modules to build/modify

1. **`shallot-radio/fido_bridge.py`** (NEW) — USB-serial bridge between PAW and FIDO Key.
   - PAW sends: `SIGN <nonce_hex> <day_hex>\n`
   - FIDO Key replies: `<signature_hex>\n`
   - Timeout: 500ms. On timeout, return None.
   - Uses `board.UART` or `usb_cdc` on RP2350.

2. **`shallot-radio/epoch.py`** (NEW) — HMAC signing and verification.
   - `sign_hmac(secret: bytes, msg: bytes) -> bytes(32)` — HMAC-SHA256.
   - `verify_hmac(secret: bytes, msg: bytes, expected: bytes) -> bool` — constant-time compare.
   - Uses `hmac` + `hashlib` (available in CircuitPython).

3. **`shallot-radio/storage.py`** (NEW) — Flash storage for enrolled keys and epoch.
   - `load_enrolled() -> dict` — reads `enrolled.json` from flash.
   - `save_enrolled(data: dict)` — writes `enrolled.json` to flash.
   - `load_epoch() -> dict` — reads `epoch.json` (secret, valid_until, day).
   - `save_epoch(data: dict)` — writes `epoch.json` to flash.
   - Cap: 16 enrolled badges max.

4. **`shallot-radio/provisioning.py`** (NEW) — Serial command parser for ENROLL/REVOKE.
   - Parses JSON lines: `{"cmd": "ENROLL", "badge_id": "001", "pub_key": "<hex>"}` and `{"cmd": "REVOKE", "badge_id": "001"}`.
   - Only active when provisioning GPIO is LOW.
   - Replies `OK\n` or `ERROR <reason>\n`.

5. **`shallot-radio/display.py`** (NEW) — E-ink display driver.
   - `show_on_site(node_id: bytes)` — show credentials + node_id.
   - `show_off_site()` — clear or show generic branding.
   - `show_granted()` — show "Access Granted".
   - `show_denied()` — show "Access Denied".
   - Uses `adafruit_epd` library for Feather RP2350 + Waveshare E-ink.

6. **`shallot-radio/button.py`** (NEW) — Button handler with debounce.
   - Uses hardware interrupt on BOOT button.
   - Debounce: 50ms.
   - Calls `paw.on_button_press()` on valid press.

7. **`shallot-radio/audit.py`** (NEW) — Access decision logging.
   - `log_access(badge_id, node_id, decision, rssi, timestamp)` — appends to `audit.jsonl`.
   - Used by Field Node after each auth attempt.

8. **`shallot-radio/fieldnode_main.py`** (MODIFY) — Replace stubs with real implementations.
   - Wire up `verify_fn` to `epoch.verify_hmac`.
   - Wire up `get_keys_fn` to `storage.load_enrolled`.
   - Wire up `get_day_fn` to `storage.load_epoch`.
   - Add provisioning mode (GPIO check + serial parser).
   - Add audit logging.

9. **`shallot-radio/paw_main.py`** (MODIFY) — Replace stubs with real implementations.
   - Wire up `sign_fn` to `fido_bridge.sign`.
   - Wire up `get_day_fn` to `storage.load_epoch`.
   - Wire up `on_state_change` to `display` updates.
   - Add button handler.
   - Add provisioning mode (serial receive for epoch sync).

10. **`shallot-radio/tests/test_epoch.py`** (NEW) — Tests for HMAC signing/verification.
11. **`shallot-radio/tests/test_storage.py`** (NEW) — Tests for flash storage.
12. **`shallot-radio/tests/test_provisioning.py`** (NEW) — Tests for serial command parsing.
13. **`shallot-radio/tests/test_integration.py`** (NEW) — E2E test with mocks.

### Interfaces

- `fido_bridge.sign(nonce: int, day: int) -> Optional[bytes]` — returns 32-byte signature or None.
- `epoch.sign_hmac(secret: bytes, msg: bytes) -> bytes` — returns 32-byte HMAC.
- `epoch.verify_hmac(secret: bytes, msg: bytes, expected: bytes) -> bool` — constant-time verify.
- `storage.load_enrolled() -> dict` — returns `{badge_id: {"pubkey": bytes, "epoch_secret": bytes, "valid_until": int}}`.
- `storage.save_enrolled(data: dict)` — writes to flash.
- `provisioning.parse_command(line: str) -> Optional[dict]` — returns parsed command or None.
- `display.show_on_site(node_id: bytes)` — updates E-ink.
- `button.on_press(callback: Callable)` — registers interrupt handler.
- `audit.log_access(badge_id, node_id, decision, rssi, timestamp)` — appends to log.

### Architectural decisions

- **Single responsibility:** Each new module handles one concern (signing, storage, display, etc.).
- **Dependency injection:** State machines receive callbacks (`verify_fn`, `sign_fn`, etc.) — no hard dependencies.
- **Fail-closed default:** All stubs return None/False. Real implementations must explicitly succeed.
- **Provisioning mode:** GPIO-controlled. Only active during physical setup. Operation mode ignores all serial commands.
- **Flash storage:** JSON files on CircuitPython's `storage` mount. Simple, debuggable, no database.
- **Audit log:** JSONL (one JSON object per line). Append-only. Consumed by thesis report.

## Testing Decisions

- **Test external behavior, not implementation details.** Test that verify_hmac returns True for valid signatures, not how it internally compares bytes.
- **Mock hardware.** Tests use mock radio, relay, display, and FIDO Key. No real hardware needed for unit tests.
- **Integration test.** One test that wires everything together with mocks and runs the full flow.
- **Prior art:** `tests/test_radio.py` already tests pack/unpack. Follow the same pattern.

### Modules to test

- `epoch.py` — HMAC sign/verify with known test vectors.
- `storage.py` — Load/save with temp directory.
- `provisioning.py` — Parse ENROLL/REVOKE commands, reject invalid.
- `integration.py` — Full flow: button → sign → send → verify → relay.

## Out of Scope

- Real FIDO2 signing (using PicoFIDO's HMAC-Secret extension). The MVP uses a software HMAC stand-in. Real FIDO2 signing is future work.
- E-ink display driver implementation. The spec defines the interface; the actual driver depends on the specific E-ink module (Waveshare variant TBD).
- Mama Bear firmware (Arduino UNO Q). The spec defines the serial protocol; the actual Mama Bear Python script is a separate task.
- Dashboard or web UI. The audit log is file-based; visualization is future work.
- Custom PCB. The prototype uses breadboards and dev boards.
- UWB secure ranging. Out of budget and scope.

## Further Notes

- The transit-protocol-mvp.md defines the full protocol contract. This spec covers the firmware implementation of that contract.
- The state machines (`state_machine.py`) are already built and tested. This spec fills in the stubs they depend on.
- The radio layer (`shallot_radio.py`) is already built and tested. This spec does not modify it.
- The pin maps (`hardware_pins.py`) are already built. This spec does not modify them.
- The existing tests (`test_radio.py`) should continue to pass. New tests are additive.
