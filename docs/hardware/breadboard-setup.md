# SHALLOT — Breadboard Setup Guide

> Step-by-step bring-up for the breadboard prototypes (PAW badge + field node).
> Order matters: each phase is verifiable before starting the next.
>
> Sources: `shallot-radio/hardware_pins.py`, `shallot-radio/fieldnode_main.py`,
> `docs/specs/firmware-integration.md`, `docs/HARDWARE-STATUS.md`.
>
> **Note:** Pin maps below follow the code (`hardware_pins.py`) — NOT the older
> proposed map in `components.md` §13. The code is authoritative.

---

## Step 0 — Software pre-flight (no hardware)

Run the mocked test suite on your laptop first:

```bash
cd yh-cybersec-prototype
pytest shallot-radio/tests/
```

All tests use mock radio/display/FIDO — no hardware needed.
Green here confirms the protocol + state machine layer before you touch a wire.

**Checkpoint:** all tests pass.

## Step 1 — Flash CircuitPython (both MCUs)

Boards: **Adafruit Feather RP2350** (PAW) and **Raspberry Pi Pico 2 W** (field node).

1. Download the **CircuitPython 9.x UF2** for each board from circuitpython.org.
2. Hold **BOOTSEL**, plug in USB → board appears as `RPI-RP2` drive.
3. Drag the UF2 onto the drive. Board reboots as `CIRCUITPY`.
4. Open the serial REPL at **115200 baud** to confirm it boots.

**Checkpoint:** REPL prompt (`>>>`) visible on both boards.

## Step 2 — Breadboard the Field Node (Pico 2 W + SX1262)

Wire exactly per `FIELDNODE_PINS` (`shallot-radio/hardware_pins.py:20-28`):

```
SX1262         Pico 2 W          SX1262         Pico 2 W
──────         ────────          ────────       ────────
VCC     →      3V3 (OUT!)        RST     →      GP15
GND     →      GND               DIO1    →      GP20
SCK     →      GP18              BUSY    →      GP21
MOSI    →      GP19              NSS/CS  →      GP17
MISO    →      GP16
```

Plus:

- **100 nF decoupling cap** directly across SX1262 VCC–GND (mandatory,
  see `components.md` §13).
- **Antenna connected BEFORE powering TX** — transmitting without an antenna
  can destroy the PA.
- Relay module input → **GP14**
- Provisioning jumper/button: **GP0 ↔ GND** (LOW = provisioning mode,
  `fieldnode_main.py:40`)
- All grounds common.

⚠️ SX1262 VCC is **3.3V only — NEVER 5V**. Check BUSY pin between SPI commands.

**Checkpoint:** wiring double-checked against the table above.

## Step 3 — Deploy Field Node firmware

Copy onto the `CIRCUITPY` drive:

1. All of `shallot-radio/*.py` → root of the drive (or `/lib`).
2. `adafruit_sx1262.mpy` from the CircuitPython library bundle → `/lib`.
3. A **`boot.py`** containing:

   ```python
   import usb_cdc
   usb_cdc.enable(console=True, data=True)
   ```

   Without this, `usb_cdc.data` is `None` and provisioning will crash
   (`fieldnode_main.py:47`).
4. Entry point logic as `code.py`.

**Checkpoint:** REPL shows the FSM ticking; no `ImportError`.

## Step 4 — Radio smoke test

Before adding e-paper/FIDO complexity:

1. Temporarily load a minimal sender script on the second radio setup
   (or swap roles).
2. Send one beacon:
   `ShallotRadio.send_beacon(b"FN01", ts, nonce)`
3. Confirm `receive()` on the field node returns
   `(MSG_BEACON, {...}, rssi)`.
4. Verify 868 MHz parameters match `constants.py`
   (`LORA_FREQUENCY_MHZ`, SF, BW, coding rate).

**Checkpoint:** one-way beacon link verified.

## Step 5 — Breadboard the PAW (Feather RP2350)

Per `PAW_PINS` (`shallot-radio/hardware_pins.py:8-16`):

```
SX1262         Feather RP2350
──────         ──────────────
VCC     →      3V3 (OUT!)
GND     →      GND
SCK     →      SCK
MOSI    →      MOSI
MISO    →      MISO
NSS/CS  →      D5
RST     →      D6
DIO1    →      D9
BUSY    →      D10
```

Same rules: 100 nF cap, antenna before TX, 3.3V only.

Deploy `paw_main.py` the same way as Step 3. Repeat the Step 4 smoke test
in the opposite direction.

**Checkpoint:** two-way beacon link verified.

## Step 6 — Provisioning round-trip

1. Jumper **GP0→GND** on the field node (enters provisioning mode).
2. From your laptop, open the `usb_cdc.data` serial port and send:

   ```json
   {"cmd": "ENROLL", "badge_id": "PAW1", "pub_key": "<hex>", "epoch_secret": "<hex>", "valid_until": <day>}
   ```

3. Expect `OK\n` reply.
4. Remove the jumper → normal operation. Heartbeats from the PAW should now
   authenticate and fire the relay.

**Checkpoint:** ENROLL accepted, relay fires on valid heartbeat.

## Step 7 — Gateway & full loop (deferred)

UNO Q Mama Bear firmware is 🔴 not started (`docs/specs/prototype-scope.md`).

Until then, run the cub-agent stack standalone on Fedora:

```bash
podman compose -f shallot-infra/compose.yml up
```

And validate the ESP32-S3 badge (pico-fido2) against the Flask demo server:

```bash
python demo/app.py   # then register/authenticate at localhost:8000
```

Open item per HARDWARE-STATUS.md: verify DIRECT attestation requirement
against the real ESP32 device.

---

## Quick reference — critical rules

| Rule | Why |
|------|-----|
| SX1262 VCC = 3.3V, never 5V | Destroys the module |
| Antenna attached before any TX | TX without antenna kills the PA |
| 100 nF decoupling cap on SX1262 VCC | SPI stability |
| Separate CS pins on shared SPI bus | Bus contention |
| Check BUSY pin between SX1262 commands | Module protocol |
| `boot.py` enables `usb_cdc.data` | Provisioning serial otherwise None |
| Provisioning only when GP0 LOW | ENROLL rejected in normal operation |
