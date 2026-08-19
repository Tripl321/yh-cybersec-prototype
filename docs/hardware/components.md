# SHALLOT Components Database

> Structured knowledge base for all hardware components in the SHALLOT project.
> Purpose: provide opencode with quick access to pinouts, specs, protocols, and status.
>
> **Lägga till material?** Se `docs/hardware/README.md` och kör `process-material.py`.

## Quick Reference

| Component | Role | Protocol | Power | Status |
|-----------|------|----------|-------|--------|
| ESP32-S3-nano + pico-fido2 | ID-bricka (PicoFIDO) | USB HID | 3.3V LiPo | ✅ Flashad + validerad |
| RP2350 8MB dev-board | Field node | LoRa SX1262 | 3.3V LiPo (inbyggd laddning) | 🟡 Inköpt |
| Arduino UNO Q | Mama bear (gateway) | LoRa SX1262, USB Serial | 5V USB | 🟡 Inköpt |
| LoRa Core1262-HF (SX1262) | Radio heartbeat | SPI | 3.3V | 🟡 Inköpt (×2) |
| 1.54" E-papper | Badge display | SPI | 3.3V | 🟡 Inköpt |
| LiPo 400 mAh | Badge power | — | 3.7V | 🟡 Inköpt |

---

## 1. ESP32-S3-nano + pico-fido2 (ID-bricka / PicoFIDO)

**Role:** FIDO2 authenticator — proves identity cryptographically via WebAuthn/CTAP 2.2.

**Specifications:**
- MCU: ESP32-S3-nano (dual-core, 240 MHz, 512 KB SRAM, 8 MB flash)
- Firmware: `pico-fido2` ([polhenarejos/pico-fido2](https://github.com/polhenarejos/pico-fido2))
- Crypto: ECDSA, EdDSA, secp256r1/256k1/384r1/521r1, Ed25519
- CTAP: 2.1 / 2.2, USB HID transport
- Attestation: self/single attestation with bundled x509 cert
- User Presence: physical button (mandatory)
- User Verification: PIN (optional, not tested)

**Pinout (ESP32-S3-nano):**
- USB: Native USB HID (D+/D-)
- GPIO: Standard ESP32-S3 pins (check board schematic)
- Button: User presence button (mapped in firmware)

**Communication:**
- To field node: USB HID (direct connection)
- Protocols: CTAP2 over USB HID (usage page 0xF1D0)

**Power:**
- Operating voltage: 3.3V
- LiPo: Can be powered via LiPo (check board LiPo connector)
- Consumption: ~20 mA active, ~5 µA deep sleep

**Status:**
- ✅ Flashad med pico-fido2
- ✅ Registrerad mot demo-servern över USB HID
- 🟡 Attestation (DIRECT) ej verifierad — servern kräver packed/self
- ❌ User Verification (PIN) ej testat
- ❌ Resident/discoverable credentials ej testat

**Notes:**
- PicoFIDO-rollen drivs av ESP32-S3-nano (INTE RP2350)
- pico-fido2 bygger på Pico SDK — ESP32-porten bekräftas vidare
- BLE/NFC saknas i pico-fido2

**Firmware:**
- Source: `polhenarejos/pico-fido2` (GitHub)
- Prebuilt UF2: `pico_fido2_pico-7.0.uf2` (för Pico 2 — bekräfta ESP32-kompatibilitet)
- Flashning: via USB DFU eller BOOT-knapp

---

## 2. RP2350 8MB dev-board (Field node)

**Role:** Field node — receives badge authentication, forwards heartbeat to gateway via LoRa.

**Specifications:**
- MCU: RP2350 (Raspberry Pi Pico 2, dual-core Arm Cortex-M33 + RISC-V, 150 MHz)
- Flash: 8 MB
- Features: Qwiic connector, LiPo-port (inbyggd TP4056-laddning)
- Board: Arduino-compatible dev-board (Eletrokit art. 41036299)

**Pinout (RP2350):**
- SPI (for LoRa SX1262):
  - SCK: GP10 (default SPI0 SCK)
  - MOSI: GP11 (default SPI0 TX)
  - MISO: GP12 (default SPI0 RX)
  - CS: GP13 (configurable)
  - RST: GP14 (configurable)
  - IRQ: GP15 (configurable)
- I2C (for Qwiic): SDA GP4, SCL GP5
- USB: Native USB (for debugging/programming)
- LiPo: JST-PH connector (inbyggd laddning via USB)
- GPIO: 30 pins (3.3V logic)

**Communication:**
- To badge: USB HID (via pico-fido2 firmware on ESP32, not RP2350)
- To gateway: LoRa SX1262 (SPI)
- To laptop: USB Serial (debugging)

**Power:**
- Operating voltage: 3.3V (buck-boost from VSYS)
- LiPo: 3.7V 400 mAh (JST-PH)
- Charging: Inbyggd via USB (TP4056 ej nödvändig)
- Consumption: ~15 mA active (RP2350), ~100 mA peak (LoRa TX)

**Status:**
- 🟡 Inköpt, ej påbörjad
- Roll: Field node (ej tilldelad ännu)

**Notes:**
- RP2350 dev-boardet har inbyggd LiPo-laddning — enklare än Pico 2 W
- Qwiic-connector för tillbehör (e-ink, sensorer)
- Pico SDK-kompatibel (C/C++ eller MicroPython)

---

## 3. Arduino UNO Q (Mama bear / Gateway)

**Role:** Gateway — receives LoRa heartbeat from field nodes, forwards to cub-agent on Fedora.

**Specifications:**
- MCU: Arduino UNO Q (4 GB — oklar om detta är lagringsutrymme eller modellbeteckning)
- Features: USB Serial, GPIO, SPI, I2C
- Board: Arduino UNO-formfaktor

**Pinout (Arduino UNO Q):**
- SPI (for LoRa SX1262):
  - SCK: D13 (default)
  - MOSI: D11 (default)
  - MISO: D12 (default)
  - CS: D10 (configurable)
  - RST: D9 (configurable)
  - IRQ: D2 (configurable, interrupt-capable)
- Serial: D0 (RX), D1 (TX) — USB Serial
- GPIO: D0-D13, A0-A5
- 5V pin: 5V output (from USB)
- 3.3V pin: 3.3V output (from regulator)

**Communication:**
- To field node: LoRa SX1262 (SPI)
- To laptop: USB Serial (to cub-agent on Fedora)
- Protocols: LoRa (868 MHz ISM), Serial (115200 baud)

**Power:**
- Operating voltage: 5V (USB) or 7-12V (DC jack)
- Consumption: ~50 mA (USB powered)
- Note: 5V logik — Level shifter behövs EJ för SX1262 (3.3V tolerant)

**Status:**
- 🟡 Inköpt, ej påbörjad

**Notes:**
- Drivs från USB — ingen batteri behövs för gateway
- 5V logik, men SX1262 är 3.3V tolerant — anslut direkt
- MOSFET-styrning för fläkt: GPIO → 150Ω → Gate (se §4)

---

## 4. LoRa Core1262-HF (SX1262) × 2

**Role:** Radio — krypterad heartbeat mellan field node och gateway.

**Specifications:**
- Chip: Semtech SX1262
- Frequency: 868 MHz ISM (EU, licensfri)
- Modulation: LoRa CSS
- Range: ~500 m LoS, ~100 m urban
- Sensitivity: -120 dBm (SF12, 125 kHz BW)
- TX power: up to +22 dBm
- Encryption: Hardware AES-128 (inbyggt i SX1262)
- Interface: SPI
- Antenna: uFL connector (FPC-antenn eller SMA-adapter)

**Pinout (Core1262-HF module):**
- VCC: 3.3V (INTE 5V!)
- GND: GND
- SPI:
  - SCK: Module pin (see datasheet)
  - MOSI: Module pin
  - MISO: Module pin
  - NSS/CS: Module pin
  - RST: Module pin (reset, active low)
  - DIO1/IRQ: Module pin (interrupt)
  - BUSY: Module pin (wait before next command)

**Connection to RP2350:**
```
SX1262          RP2350
------          ------
VCC      →      3V3 (NOT 5V!)
GND      →      GND
SCK      →      GP10 (SPI0 SCK)
MOSI     →      GP11 (SPI0 TX)
MISO     →      GP12 (SPI0 RX)
CS/NSS   →      GP13
RST      →      GP14
DIO1/IRQ →      GP15
BUSY     →      GP16 (read before next cmd)
```

**Connection to Arduino UNO Q:**
```
SX1262          UNO Q
------          -----
VCC      →      3.3V (NOT 5V!)
GND      →      GND
SCK      →      D13 (SPI SCK)
MOSI     →      D11 (SPI MOSI)
MISO     →      D12 (SPI MISO)
CS/NSS   →      D10
RST      →      D9
DIO1/IRQ →      D2 (interrupt)
BUSY     →      D3 (read before next cmd)
```

**Power:**
- Operating voltage: 3.3V (MAX 3.6V — DO NOT connect to 5V!)
- Consumption: ~5 mA RX, ~120 mA TX (+22 dBm), ~0.2 µA sleep
- Note: Use 3.3V pin from Arduino, NOT 5V pin

**Status:**
- 🟡 Inköpt (×2), ej påbörjad
- Antenner: FPC uFL 1.8 dBi + SMA 3 dBi + SMA→uFL adapter

**Notes:**
- Hardware AES-128 — kan användas för Transit-protokollets kryptering
- SF7-SF12 (spreading factor) — högre SF = längre räckvidd + långsammare
- LoRaWAN ej använt — punkt-till-punkt (enklast)
- Duty cycle: 1% på 868 MHz (EU-regler) — heartbeat var 10:e sekund OK

---

## 5. 1.54" E-papper (Badge Display)

**Role:** Displays badge status (ID, access state, lockout).

**Specifications:**
- Size: 1.54"
- Resolution: 200×200 px
- Colors: Black, White, Red (tri-color)
- Interface: SPI
- Refresh: ~2 s full, ~0.3 s partial
- Power: <0.01 µA standby (image persists)

**Pinout (typical e-paper module):**
- VCC: 3.3V
- GND: GND
- DIN/MOSI: SPI data
- CLK/SCK: SPI clock
- CS: Chip select (active low)
- DC: Data/Command select
- RST: Reset (active low)
- BUSY: Busy signal (wait for refresh)

**Connection to RP2350:**
```
E-paper        RP2350
--------       ------
VCC     →      3V3
GND     →      GND
DIN     →      GP11 (SPI0 MOSI, shared with LoRa?)
CLK     →      GP10 (SPI0 SCK, shared with LoRa?)
CS      →      GP17 (separate from LoRa CS)
DC      →      GP18
RST     →      GP19
BUSY    →      GP20
```

**Note:** SPI sharing with LoRa — use separate CS pins. E-ink refresh is slow; avoid during LoRa transmission.

**Power:**
- Operating voltage: 3.3V
- Consumption: ~26 mW during refresh, ~0 µA standby

**Status:**
- 🟡 Inköpt, ej påbörjad

---

## 6. LiPo 400 mAh (Badge Power)

**Role:** Powers the badge (ESP32 + LoRa + e-ink).

**Specifications:**
- Chemistry: LiPo (Lithium Polymer)
- Voltage: 3.7V nominal (3.0V cutoff, 4.2V full)
- Capacity: 400 mAh (1.48 Wh)
- Connector: JST-PH 2.0 mm
- Protection: PCM (over-charge, over-discharge, short circuit)

**Connection:**
- To RP2350 dev-board: JST-PH → board's LiPo connector
- Charging: Via USB on RP2350 board (inbyggd TP4056)

**Runtime estimates:**
- ESP32 (PicoFIDO) + LoRa heartbeat (every 10s):
  - ESP32 active: ~20 mA
  - LoRa TX peak: ~120 mA (100 ms every 10s = ~1.2 mA avg)
  - Total: ~22 mA average
  - Runtime: 400 mAh / 22 mA ≈ **18 hours** (continuous use)
- With deep sleep between heartbeats: **days** (取决于 sleep current)

**Status:**
- 🟡 Inköpt, ej påbörjad

**Notes:**
- RP2350 dev-boardet laddar cellen via USB — TP4056 ej nödvändig
- PCM-skydd ingår — ingen extern skyddskrets behövs

---

## 7. Passiva komponenter och tillbehör

### Kondensatorer
| Type | Value | Voltage | Qty | Notes |
|------|-------|---------|-----|-------|
| Keramisk | 100 nF | 50V | 5 | Decoupling (bypass) på VCC |
| Elektrolyt | 47 µF | 25V | 20 | Bulk decoupling |
| Elektrolyt | 10 µF | 25V | 25 | Intermediate decoupling |

### Motstånd
| Value | Tolerance | Qty | Notes |
|-------|-----------|-----|-------|
| 4.7 kΩ | 1% | 10 | Pull-up/pull-down, I2C |
| 330 Ω | — | 10 | LED current limiting, MOSFET gate |

### Övrigt
| Component | Qty | Notes |
|-----------|-----|-------|
| Stiftlist 2.54 mm 1×40 | 4 | Breakable headers |
| Experimentkort 80×120 mm | 1 | Prototyping |
| Experimentkort 70×90 mm | 1 | Prototyping |
| Distanshylsa M2.5 10 mm | 6 | Mounting |
| Kopplingstråd solid 10 färger | 1 set | Wiring |
| Vippströmställare SPDT | 1 | Power on/off |
| Temperatursensor DS18B20 | 1 | Environmental monitoring (optional) |
| Adapterkabel SMA→uFL | 1 | Antenna adapter |

---

## 8. Antenner

### FPC Antenn 868 MHz (Badge)
- Type: FPC (flexible PCB)
- Gain: 1.8 dBi
- Connector: uFL
- Mounting: Inside badge enclosure
- Notes: RF-transparent through wood/veneer

### SMA Antenn 3 dBi (Gateway)
- Type: Duck/whip
- Gain: 3 dBi
- Connector: SMA male
- Mounting: External on gateway
- Notes: Higher gain for better range

### SMA→uFL Adapter
- Type: Cable adapter
- Length: 100 mm
- Notes: Connects SMA antenna to uFL module

---

## 9. MOSFET + Fläkt (Thermal Management)

**Role:** Controls 40 mm fan in badge enclosure (if needed).

**MOSFET: 30N06L (N-channel, logic-level)**
- V_DS max: 60V
- I_D max: 30A
- R_DS(on): <0.047Ω @ V_GS=10V
- V_GS(th): 1-2V (logic-level — driven by 3.3V/5V GPIO)
- Package: TO-220 (Pin 1=Gate, 2=Drain, 3=Source)

**Fan: Noctua NF-A4x10 FLX**
- Size: 40 mm
- Voltage: 12V
- Current: 0.05A max (0.6W)
- Speed: 4500 RPM
- Connector: 3-pin (tach output)
- Note: Requires 12V supply — NOT from Arduino 5V

**Circuit (low-side switch):**
```
12V+  ────[Fan red (+)]────[Fan black (-)]──── MOSFET Drain
                                                      │
GND (12V-) ────────────────────────────────────── MOSFET Source
                                                      │
Arduino GPIO ──[150Ω]── MOSFET Gate
                              │
                        [10kΩ pull-down]── GND (optional)

1N4007 flyback diode: Cathode → 12V+, Anode → Drain
```

**Control:**
- `digitalWrite(pin, HIGH)` = Fan ON
- `digitalWrite(pin, LOW)` = Fan OFF
- PWM on Gate for speed control (optional)

**Status:**
- 🟡 MOSFET + fläkt inköpt/planerad, ej monterad

---

## 10. System Topology

```
┌─────────────────────┐
│   ESP32-S3-nano     │
│   + pico-fido2      │
│   (ID-bricka)       │
│                     │
│  [USB HID]──────────┼──┐
│                     │  │
│  [Button] = UP      │  │
└─────────────────────┘  │
                         │
┌─────────────────────┐  │
│   RP2350 8MB        │◄─┘
│   (Field node)      │
│                     │
│  [LoRa SX1262]──────┼──┐
│                     │  │
│  [E-paper] = Status │  │
│  [LiPo 400mAh]     │  │
└─────────────────────┘  │
                         │ (868 MHz LoRa)
┌─────────────────────┐  │
│   Arduino UNO Q     │◄─┘
│   (Mama bear)       │
│                     │
│  [LoRa SX1262]──────┼──┐
│  [USB Serial]───────┼──┼──┐
└─────────────────────┘  │  │
                         │  │
┌─────────────────────┐  │  │
│   Fedora laptop     │◄─┘  │
│   (Cub-agent)       │◄────┘
│                     │
│  [Ollama] = LLM     │
│  [API] → OT device  │
└─────────────────────┘
```

---

## 11. Protocol Stack

```
Layer           Component           Protocol
─────           ─────────           ────────
Application     Cub-agent           Python HTTP API
Transport       USB Serial          UART 115200 baud
Network         LoRa SX1262         LoRa CSS (868 MHz)
Data Link       SX1262              Custom (Transit heartbeat)
Physical        SX1262              868 MHz ISM RF
─────           ─────────           ────────
Application     WebAuthn RP         Flask + webauthn library
Transport       USB HID             CTAP2 over HID
Physical        ESP32 USB           USB 2.0 Full Speed
```

---

## 12. Power Budget

| Component | Active (mA) | Sleep (µA) | Notes |
|-----------|-------------|------------|-------|
| ESP32-S3 (PicoFIDO) | 20 | 5 | Active during auth |
| RP2350 (Field node) | 15 | 3 | Always-on (heartbeat listener) |
| SX1262 (LoRa TX) | 120 | 0.2 | 100 ms TX burst every 10s |
| SX1262 (LoRa RX) | 5 | 0.2 | Listening mode |
| E-paper (refresh) | 15 | 0.01 | 2s refresh, then standby |
| DS18B20 (temp sensor) | 1 | 0.001 | Optional |
| **Badge total** | ~37 | ~8 | ESP32 + LoRa TX avg + e-ink |
| **Gateway total** | ~50 | — | UNO Q + LoRa RX (USB powered) |

**Badge runtime (LiPo 400 mAh):**
- Continuous: 400 mAh / 37 mA ≈ **10.8 hours**
- With sleep: 400 mAh / 5 mA avg ≈ **80 hours** (3+ days)

---

## 13. Important Notes for opencode

**DO:**
- Use 3.3V for SX1262 — NEVER connect to 5V
- Check BUSY pin before sending next SPI command to SX1262
- Use separate CS pins when sharing SPI bus (LoRa + e-ink)
- Wait for e-paper BUSY pin to go LOW before next operation
- Use hardware AES-128 in SX1262 for Transit encryption

**DON'T:**
- Connect SX1262 VCC to 5V (will destroy the module)
- Share SPI without separate CS pins (bus contention)
- Refresh e-paper during LoRa transmission (SPI conflict)
- Forget the 100 nF decoupling caps on VCC pins
- Use PWM on 3-pin fan without checking MOSFET gate voltage

**Pin allocation (proposed):**
```
RP2350 (Field node):
  GP10-13: SPI0 (LoRa SX1262)
  GP14: LoRa RST
  GP15: LoRa DIO1/IRQ
  GP16: LoRa BUSY
  GP17: E-paper CS
  GP18: E-paper DC
  GP19: E-paper RST
  GP20: E-paper BUSY
  GP11: SPI0 MOSI (shared: LoRa + E-paper)
  GP10: SPI0 SCK (shared: LoRa + E-paper)

Arduino UNO Q (Gateway):
  D13: SPI SCK (LoRa)
  D12: SPI MISO (LoRa)
  D11: SPI MOSI (LoRa)
  D10: LoRa CS
  D9: LoRa RST
  D2: LoRa DIO1/IRQ (interrupt)
  D3: LoRa BUSY
  D0/D1: USB Serial (to Fedora)
  D5: MOSFET Gate (fan control, optional)
```
