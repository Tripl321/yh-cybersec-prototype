# System Specification & Architecture: Project SHALLOT

Secure Hardware-Assisted Local LoRa Trust (Industrial IAM Framework)

## 1. Executive Summary & Product Vision

SHALLOT is an air-gapped, zero-trust Industrial Identity and Access Management (IAM) framework designed for manufacturing environments (such as discrete industrial cells in Dalarna). It replaces vulnerable static badges and unsecured 2.4GHz wireless tags with a Continuous Presence and Context-Aware Access Control system.

The system utilizes sub-GHz LoRa (Chirp Spread Spectrum) combined with FIDO2/HMAC cryptographic handshakes, physical "User Presence" validation, and dynamic E-ink privacy masking to secure both plant-level operational security (OPSEC) and machine-level (PLC) safety.

## 2. Hardware Manifest & Physical Architecture

### Mama Bear (Central Provisioning Hub)

- **Hardware:** Arduino UNO Q (Debian/Python core).
- **Role:** Air-gapped root of trust. No wireless radios. Handles initial provisioning and rolling token sync via physical wired serial interface.
- **Enclosure:** Desktop dock design (wood/acrylic integration with a physical master power toggle switch).

### PAW - Personal Access Wearable (The Smart Badge)

- **Hardware:** Adafruit Feather RP2350, Core1262-HF LoRa module, E-ink display, 400mAh LiPo battery, physical button.
- **Role:** Dynamic identity token. Displays contextual status, manages macro/micro presence, and orchestrates cryptographic handshakes via the FIDO-Key.
- **Enclosure:** Custom "wooden sandwich" multi-layer fine-wood craftsmanship enclosure with flush-mounted E-ink display.

### FIDO-Key (Cryptographic Authenticator)

- **Hardware:** ESP32-S3-Nano (PicoFIDO firmware).
- **Role:** Removable cryptographic module. Stores the FIDO2 private key and produces signed assertions. Plugs into the PAW via serial (USB/UART). The PAW never holds the private key directly.
- **Trust model:** The FIDO-Key is the root of cryptographic trust. If separated from the PAW, it cannot operate (no display/radio/button). If the PAW is stolen without the FIDO-Key, it cannot sign heartbeats.

### Field Node - PLC Sentinel (Machine Guard)

- **Hardware:** Raspberry Pi Pico 2 W + Core1262-HF LoRa module + Relay/LED output.
- **Role:** Edge-enforcement node mounted directly on industrial machinery. Executes fail-closed watchdog logic based on continuous cryptographic heartbeat and RSSI proximity gating.

## 3. Core Operational Modes & Security Logic

### A. Macro-Presence (Geofencing & OPSEC)

**Mechanism:** The Field Node continuously broadcasts a low-power encrypted beacon.

**State Trigger:** When the PAW receives the beacon, it transitions from Off-Site to On-Site.

**Privacy Masking:**
- **Off-Site** (No radio contact): E-ink display is completely cleared or shows generic company branding (prevents shoulder surfing and visual tracking outside the facility).
- **On-Site:** E-ink display updates to show authorized employee credentials, name, and role.

### B. Micro-Presence & Intentional Access (PLC Sentinel)

**Mechanism:** To unlock a hazardous machine, proximity alone is insufficient.

**RSSI Gating:** Field Node requires a strong signal threshold (e.g., RSSI > -40 dBm) to ensure the operator is standing immediately in front of the machine (1-2 meter bubble).

**User Presence (FIDO2 Principle):** The user must physically press and hold the onboard BOOT button on the PAW at the moment of the handshake. This prevents relay attacks or unauthorized usage of a dropped badge.

**Fail-Closed Watchdog:** If the periodic heartbeat is lost for >5 seconds or the operator steps away (RSSI < -70 dBm), the Field Node immediately trips the safety relay (fails closed).

### C. Out-of-Band (OOB) Wired Provisioning & Epoch Sync

**Security Principle:** Zero wireless provisioning to eliminate remote basestation spoofing.

**Workflow:**
1. Mama Bear generates an encrypted rolling schedule/token list (Epoch file) locally.
2. During shift changes or weekly maintenance, the PAW and Field Nodes are physically tethered to Mama Bear via USB-serial.
3. Credentials and expiration schedules are synced via structured JSON payloads over the serial bus.

## 4. Technical Stack & Implementation Guidelines

- **Languages:** Python (Mama Bear provisioning scripts) / CircuitPython or MicroPython (ESP32-S3 / RP2350 runtime logic for rapid iteration).
- **Radio Stack:** RadioLib (C/C++) or equivalent lightweight SPI LoRa driver. Strictly Point-to-Point (PHY layer); avoid complex LoRaWAN protocol stacks to maintain 4-week MVP feasibility.
- **Cryptography:** Standard HMAC-SHA256 timestamped challenge-response payloads to sign heartbeats.
- **Display Management:** Waveshare e-Paper drivers configured to minimize full-refresh flicker during status updates.

## 5. 4-Week PoC Sprint Objectives ("Smoke & Mirrors" MVP)

**Week 1 (Radio Link):** Establish reliable SPI communication between Feather RP2350 (PAW) and Pico 2 W (Field Node) via Core1262-HF modules using point-to-point packets.

**Week 2 (Watchdog & UI):** Implement the fail-closed timer loop on the RP2350 and render dynamic states (Off-Site vs On-Site) on the E-ink display.

**Week 3 (Access Control & Button):** Integrate the RSSI threshold check and the physical BOOT button press as a mandatory requirement for the handshake.

**Week 4 (Provisioning & Polish):** Write the Mama Bear Python script for serial JSON token pushing, assemble the physical wooden/desktop enclosures, and finalize the portfolio documentation.
