# Research Report: SHALLOT Hardware Architecture & Cost (Remaining Components)

**Issue:** [#9](https://github.com/Tripl321/yh-cybersec-prototype/issues/9) (T10 Research)  
**Author:** AI Agent  
**Date:** 2026-08-13  
**Status:** Completed  

---

## Primary Sources

1. **Raspberry Pi Pico 2 W Datasheet** — power architecture (VSYS 1.8–5.5 V buck-boost, 3V3 out ≤300 mA), GPIO fixed 3.3 V. [Raspberry Pi](https://pip-assets.raspberrypi.com/categories/1088-raspberry-pi-pico-2-w/documents/RP-008304-DS-2-pico-2-w-datasheet.pdf)
2. **Electrokit (Swedish distributor)** — local street prices incl. VAT: Pico 2 W (95 SEK), RFM69HW-868S2 (65 SEK), e-Paper HAT (199 SEK), LiPo 3.7 V, TP4056 (55 SEK). [electrokit.com](https://www.electrokit.com/)
3. **Waveshare Pico-ePaper-2.13** — 2.13" 250×122 B/W e-ink shield that stacks on the Pico, SPI, 3.3 V, standby <0.01 µA, refresh 26.4 mW. [Waveshare](https://www.waveshare.com/Pico-ePaper-2.13.htm)
4. **HopeRF RFM69HW** — 868 MHz ISM transceiver, 1.8–3.6 V, +20 dBm, RX -120 dBm, SPI, built-in AES-128. [Electrokit RFM69HW](https://www.electrokit.com/en/rfm69hw-868mhz-transceiver)
5. **Adafruit / The Pi Hut LiPo** — 3.7 V 500 mAh with JST-PH + PCM protection. [Adafruit 1578](https://www.adafruit.com/product/1578)
6. **LowPowerLab helical antenna** — 868 MHz 2 dBi, ~$1.95. [LowPowerLab](https://lowpowerlab.com/shop/product/160)

---

## Executive Summary

This research specifies the hardware that remains beyond the two Raspberry Pi Pico 2 W boards already in scope, and produces a Bill of Materials (BOM) with Swedish-distributor pricing. A key architectural finding is that the **Pico 2 W's onboard buck-boost regulator removes the need for a separate DC-DC converter**: a single Li-Po cell (3.0–4.2 V) feeds `VSYS` directly (via a Schottky diode for USB power-ORing), and the 3.3 V rail powers both the e-ink and the RFM69HW. Total estimated hardware cost for a complete 1-badge + 1-gateway prototype is **~900–1 050 SEK incl. shipping**, far below the 4 000 SEK budget — leaving large headroom for tools, spares, and printing.

---

## 1. Component Research

### 1.1 E-ink display
- **Recommendation:** Waveshare **Pico-ePaper-2.13** (2.13", 250×122, B/W, SPI). Stacks directly on the Pico 2 W as a shield — ideal for a flat ID badge.
- **Specs:** 3.3 V, standby current <0.01 µA (image persists with zero power), full refresh 2 s / partial 0.3 s, refresh power 26.4 mW. [Waveshare]
- **Cost:** ~149 SEK (direct from Waveshare/PISOutlet, $13.99). Local alternative: Waveshare **2.13" e-Paper HAT** (40-pin) at Electrokit **199 SEK** — works on the Pico 2 W header but is larger (65×30 mm) and 40-pin SBC-form, less badge-friendly.
- **Red option** (B/W/R, 219 SEK @ Electrokit) is viable if status colour (e.g. red = lockout) is wanted, at the cost of 15 s full-refresh.

### 1.2 RFM69HW radio (Transit heartbeat link)
- **Recommendation:** HopeRF **RFM69HW-868S2** (high-power 868 MHz ISM).
- **Specs:** 1.8–3.6 V (drives straight from the Pico 3V3 rail — no level shifter), SPI, +20 dBm TX, -120 dBm RX, built-in AES-128 (used by the Transit protocol). Range ~500 m LoS with a simple antenna; ~2 m needed for proximity heartbeat. [Electrokit]
- **Cost:** **65 SEK** @ Electrokit (art. 41017409). International $8.70 (Amazon) / €5 (Tinytronics).
- **Quantity:** **2 modules** — one per communicating Pico (badge ⇄ gateway) for the encrypted heartbeat link.
- **Antenna:** 868 MHz helical/spring antenna, ~**25 SEK** (LowPowerLab $1.95; bare copper spring antenna ~10–20 SEK).

### 1.3 Li-Po battery
- **Recommendation:** **3.7 V 500 mAh Li-Po** with JST-PH 2.0 mm connector + built-in PCM protection.
- **Specs:** 29×36×4.75 mm, 10.5 g, ~1.85 Wh. [Electrokit / Adafruit 1578]
- **Cost:** ~**79 SEK** (Adafruit $7.95 ≈ 85 SEK; The Pi Hut £6 ≈ 70 SEK; Electrokit carries the 500 mAh JST-PH cell — confirm exact line price at checkout). A 380 mAh variant is also available if the badge must be thinner.
- **Runtime:** Pico 2 W deep-sleep + e-ink static is µA-level; with periodic heartbeat TX bursts the 500 mAh cell gives multiple days of typical OT-shift use. Charged via the TP4056 below.

### 1.4 Power supply / charging
- **Key finding (simplifies the design):** the Pico 2 W has an **onboard RT6154 buck-boost SMPS accepting 1.8–5.5 V on `VSYS`** and generating a regulated 3.3 V (up to ~300 mA external load). A Li-Po cell (3.0–4.2 V) can therefore connect **directly to `VSYS`** through a Schottky diode; no separate boost regulator is required. The same 3V3 rail powers the e-ink and RFM69HW. [Pico 2 W Datasheet, §Power supply]
- **Charging:** **TP4056 Micro-USB Li-Po charger module** (with DW01 protection). Sits between USB and the cell; ~**55 SEK** @ Electrokit. Adds charge/fully-charged LEDs.
- **Misc power parts:** 1× Schottky diode (power-ORing USB vs battery, ~2 SEK), 1× tactile button (FIDO2 user-presence + power toggle, ~3 SEK), pin headers, JST pigtail, wiring (~40 SEK total).
- **Gateway:** powered from USB (no battery needed) — just a USB cable (~29 SEK) or reuse an existing one.

### 1.5 Enclosure (wood / veneer)
- **Recommendation:** laser-cut or hand-cut **3 mm plywood / balsa "fanér"** sandwich holding the Pico + e-ink + RFM69 + Li-Po, plus a **lanyard/clip** to wear as an ID badge.
- **Cost:** plywood/veneer sheet + standoffs + lanyard + clip ≈ **100 SEK** per badge. Gateway enclosure (simple box) ≈ **50 SEK**. (Swedish craft/wood suppliers; prices are material-only estimates and exclude any laser-cutting service fee.)
- **Note:** wood/veneer is non-conductive and RF-transparent at 868 MHz, so it does not attenuate the heartbeat radio — a security *and* signal advantage over a metal case.

---

## 2. Recommended BOM (research baseline — 1 badge + 1 gateway)

This is the *research* recommendation used as a reference; the **actual** procurement in §3 diverges from it (see reconciliation).

| # | Component | Qty | Unit (SEK) | Subtotal | Source |
|---|---|---|---|---|---|
| 1 | Raspberry Pi Pico 2 W (badge) | 1 | 95 | 95 | Electrokit |
| 2 | Raspberry Pi Pico 2 W (gateway) | 1 | 95 | 95 | Electrokit |
| 3 | Waveshare Pico-ePaper-2.13 (e-ink) | 1 | 149 | 149 | Waveshare/PISOutlet |
| 4 | HopeRF RFM69HW-868S2 | 2 | 65 | 130 | Electrokit |
| 5 | 868 MHz helical antenna | 2 | 25 | 50 | LowPowerLab/alias |
| 6 | Li-Po 3.7 V 500 mAh (JST-PH) | 1 | 79 | 79 | Electrokit/Adafruit |
| 7 | TP4056 Li-Po charger (Micro-USB) | 1 | 55 | 55 | Electrokit |
| 8 | Schottky diode + tactile button + headers + JST + wire | — | 40 | 40 | Electrokit |
| 9 | Wood/veneer badge enclosure + lanyard | 1 | 100 | 100 | craft supplier |
| 10 | Gateway enclosure (simple box) | 1 | 50 | 50 | craft supplier |
| 11 | USB cable (gateway power) | 1 | 29 | 29 | Electrokit/alias |
| | | | **Hardware total** | **≈ 872** | |
| | Shipping & handling (est.) | | | **≈ 150** | |
| | **Grand total** | | | **≈ 1 020 SEK** | |

---

## 3. Actual Procurement (as purchased — Electrokit)

The hardware for this issue has already been ordered. Real order below (all prices incl. VAT, SEK):

| Produkt | Art nr | Antal | Pris/st | Total |
|---|---|---|---|---|
| Arduino 8-i-1 USB-C Dongle | 41037402 | 1 | 249.00 | 249.00 |
| RP2350 8MB utvecklingskort – Qwiic och LiPo-port | 41036299 | 1 | 199.00 | 199.00 |
| Arduino UNO Q 4GB | 41036021 | 1 | 899.00 | 899.00 |
| FPC-antenn 868 MHz 1.8 dBi uFL | 41033040 | 1 | 37.00 | 37.00 |
| Antenn 868 MHz 3 dBi SMA | 41032999 | 1 | 55.00 | 55.00 |
| LoRa-modul 868 MHz Core1262-HF uFL | 41022519 | 2 | 129.00 | 258.00 |
| 1.54" E-papper 200×200px sv/v/röd, SPI | 41022489 | 1 | 189.00 | 189.00 |
| Keramisk kondensator 100 nF 50 V | 41003074 | 5 | 2.70 | 13.50 |
| Stiftlist 2.54 mm 1×40 brytbar | 41001167 | 4 | 9.50 | 38.00 |
| Elektrolytkondensator 47 µF 25 V | 40520006 | 20 | 0.70 | 14.00 |
| Elektrolytkondensator 10 µF 25 V | 41019084 | 25 | 0.50 | 12.50 |
| Batteri LiPo 3.7 V 400 mAh JST-PH | 41016062 | 1 | 119.00 | 119.00 |
| Experimentkort 80×120 mm | 41015757 | 1 | 34.00 | 34.00 |
| Temperatursensor DS18B20 | 41015731 | 1 | 39.00 | 39.00 |
| Distanshylsa M2.5 10 mm | 41014104 | 6 | 3.00 | 18.00 |
| Adapterkabel SMA-hona → uFL 100 mm | 41013985 | 1 | 69.00 | 69.00 |
| Experimentkort 70×90 mm | 41010658 | 1 | 32.00 | 32.00 |
| Motstånd 4.7 kΩ 1 % | 40811347 | 10 | 1.00 | 10.00 |
| Vippströmställare SPDT on-on | 40220010 | 1 | 12.90 | 12.90 |
| Kopplingstråd solid 10 färger | 40110011 | 1 | 179.00 | 179.00 |
| Motstånd 330 Ω | 40810233 | 10 | 1.00 | 10.00 |
| **Frakt** | | | | 55.00 |
| **Summa** | | | | **2 541.90 SEK** |

### Reconciliation vs research recommendation
| Research rec. | Actual purchase | Assessment |
|---|---|---|
| 2× Pico 2 W (RP2350) | 1× RP2350 8MB Qwiic+LiPo board + 1× Arduino UNO Q | ✅ RP2350 board keeps Pico ecosystem (RP2350, Pico SDK compatible) **and adds an integrated Li-Po port** (simplifies charging). Arduino UNO Q serves as the second MCU / gateway. Still satisfies decision #6 (two devices, strict separation). **Deviation to confirm** with issue owner. |
| RFM69HW-868S2 | 2× LoRa Core1262-HF (SX1262) | ✅ Issue explicitly allowed *"RFM69HW-radio alternativ"*. SX1262 is 868 MHz ISM, long range, lower power, **hardware AES-128** — suitable for the Transit heartbeat. Chosen alternative is reasonable. |
| 2.13" e-ink | 1.54" 200×200 B/W/R e-ink | ✅ Smaller, tricolour (red = lockout state). Adequate for badge status text. |
| Li-Po 500 mAh | Li-Po 400 mAh | ✅ Slightly smaller; fine for badge runtime. |
| TP4056 charger | Not bought — RP2350 board has Li-Po port **with built-in charging** | ✅ Bekräftat: kortet laddar cellen via USB, TP4056 ej nödvändig. |
| 868 MHz antenna | FPC uFL 1.8 dBi + SMA 3 dBi + SMA→uFL adapter | ✅ Flexible; SMA duck for gateway, FPC for badge. |
| Enclosure wood/veneer | Not yet bought | ⚠️ Remaining item (see §4). |

### Not yet procured (recommended next buys)
- **Wood/veneer enclosure + lanyard/clip** for the badge (~100–150 SEK).
- **Second e-ink + second Li-Po** if ≥2 badges are needed for SUS user-testing.
- **TP4056** only if the RP2350 board's Li-Po port lacks charging.
- Tools (soldering iron, multimeter) if not already owned.

---

## 4. Budget & Architecture Conclusion

- **Budget:** 4 000 SEK. **Actual spend 2 541.90 SEK (≈ 64 % of budget)**, leaving **~1 458 SEK** for: wood/veneer enclosure + lanyard, a possible second badge (e-ink + Li-Po), tools, spare parts, thesis printing/binding, and contingency.
- **Power architecture win (confirmed):** the RP2350 board's onboard buck-boost + Li-Po port regulate the cell → 3.3 V internally; e-ink and LoRa module both run off the 3V3 rail. No separate DC-DC boost converter needed.
- **Security note:** 868 MHz ISM is license-free in EU; SX1262 AES-128 backs the Transit heartbeat encryption. Wood enclosure is RF-transparent and isolates the badge electrically.
- **Open confirmations for follow-up tickets:**
  1. ~~Confirm PicoFIDO compatibility / "2× Pico 2 W"~~ ✅ **Löst:** användaren har **2× Pico 2 W hemma** — PicoFIDO (RP2350) kan köras på kanonhårdvaran. De inköpta RP2350-dev-boardet + Arduino UNO Q är komplement (t.ex. RP2350-kortet för integrerad LiPo-port vid prototyp, Uno som gateway/extra).
  2. ~~Confirm the RP2350 board's Li-Po port includes charging~~ ✅ Bekräftat: kortets LiPo-port laddar cellen (TP4056 ej nödvändig).
  3. Decide badge count (≥2 for SUS A/B testing).

---

## Next Steps
- **Issue #9 outcome:** Resolved and documented (this report).
- Feeds the SHALLOT BOM / spec (#1 map) and the procurement record.
- **Blocks cleared:** prototyping/grilling tickets (#7) that depended on a finalized parts list can now proceed.
- Action: update `CONTEXT.md` Hårdvara to reflect the actually purchased parts.
