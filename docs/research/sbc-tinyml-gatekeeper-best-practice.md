# Research Report: UNO Q 4GB — TinyML + gatekeeper på samma nod, och best practice för heartbeat/proximity + auth

**Issue:** Forskning för SHALLOT/Cub gatekeeper-arkitektur (Arduino UNO Q 4GB)
**Author:** AI Agent
**Date:** 2026-08-16
**Status:** Completed

---

## 0. Primära källor (läslista)

1. **Arduino UNO Q 4GB** — Arduino/Qualcomm primärdokumentation. [Arduino Docs UNO Q](https://docs.arduino.cc/hardware/uno-q/) · [UNO Q User Manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/) · [Qualcomm-sidan för UNO Q](https://www.qualcomm.com/developer/hardware/arduino-uno-q) · [Zephyr: UNO Q-board](https://docs.zephyrproject.org/latest/boards/arduino/uno_q/doc/index.html)
2. **Qualcomm QRB2210** — SoC-dokumentation (split-processing-design). [Qualcomm UNO Q-djupdykning](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
3. **STM32U585** — ST:s säkerhets-MCU (TrustZone, PSA Level 3 / SESIP3). [ST produkt](https://www.st.com/en/microcontrollers-microprocessors/stm32u585ai.html) · [ST: PSA Level 3 / SESIP (embedded.com)](https://www.embedded.com/stm32u5-mcus-achieve-psa-certified-level-3-and-sesip-certifications/) · [UM2852 Security guidance](https://www.st.com/resource/en/user_manual/um2852-stm32u585xx-security-guidance-for-psa-certified-level-3-with-sesip-profile-stmicroelectronics.pdf)
4. **TinyML/edge-AI på A53** — benchmarks + prestandadiskussioner. [MDPI Sensors: Isolation Forest på MCU](https://www.mdpi.com/1424-8220/23/4/2344) · [samanvya.dev: anomaly detection Pi 3B+ (indikativ, blogg)](https://samanvya.dev/blog/anomaly-detection-raspberry-pi) · [Google AI-forum: int8 vs float32 på A53](https://discuss.ai.google.dev/t/int8-tflite-model-performs-worse-than-float32-model-on-arm-cortex-a53/90390/4)
5. **PREEMPT_RT / determinism** — Linux realtidspraxis. [docs.kernel.org real-time](https://docs.kernel.org/core-api/real-time/) · [Red Hat: determinism i industriell edge](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge)
6. **NIST SP 800-63B** — autentiseringsnivåer (AAL2). [pages.nist.gov/800-63-3](https://pages.nist.gov/800-63-3/sp800-63b.html)
7. **WebAuthn / FIDO2** — RP ID-regler och origin-binding. [web.dev: RP ID](https://web.dev/articles/webauthn-rp-id) · [Yubico: RP-implementeringsguide](https://developers.yubico.com/Passkeys/Passkey_relying_party_implementation_guidance/)
8. **BLE-reläattacker** — NCC Group tekniska advisory. [NCC Group](https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/)
9. **UWB secure ranging** — FiRa-konsortiets whitepaper. [FiRa whitepaper PDF](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf) · [Ghost Peak (USENIX 2022): UWB distansreduktionsattack](https://www.usenix.org/conference/usenixsecurity22/presentation/ghost-peak)
10. **LoRa ranging** — Semtech. [Theory and principle of Advanced Ranging PDF](https://www.semtech.com/uploads/technology/LoRa/theory-and-principle-of-advanced-ranging.pdf)
11. **OT-säkerhet / zonmodell** — NIST SP 800-82r3, IEC 62443. [NIST 800-82r3 PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) · [Cisco: IEC 62443-3-3](https://www.cisco.com/c/en/us/products/collateral/security/isaiec-62443-3-3-wp.html)

---

## 1. Kort sammanfattning

- **Ja, UNO Q 4GB kan köra både TinyML och gatekeeper-tjänster samtidigt** — men med en tydlig arbetsdelning: Linux-sidan (QRB2210) gör AI-inferens, FIDO2-verifiering och policy; MCU:n (STM32U585) gör tidskritiska och fail-safe-uppgifter (hjärt-klocka, låsstyrning, watchdog). [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/) · [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- **Det räcker med små modeller för vår användning**: Isolation Forest körs till och med på en MCU (ESP32, ~84 KB RAM, <16 ms inferens); på Pi 3B+-klass (samma A53-kärnor som QRB2210) tar samma modell ~8 ms med ~60 MB RAM. En liten int8-autoencoder (~800 KB, ~40 MB RAM) ger ~12 ms. [MDPI Sensors](https://www.mdpi.com/1424-8220/23/4/2344) · [samanvya.dev](https://samanvya.dev/blog/anomaly-detection-raspberry-pi)
- **A53-kärnor har ett känt fällval**: int8-kvantiserade modeller kan bli *långsammare* än float32 (A53 saknar dot-produkt-instruktioner). Kör float32 + XNNPACK för små modeller. [Google AI-forum](https://discuss.ai.google.dev/t/int8-tflite-model-performs-worse-than-float32-model-on-arm-cortex-a53/90390/4)
- **Proximity ≠ RSSI**: BLE-baserad närhetsautentisering är reläattackbar (NCC Group), och LoRa-RSSI ger ingen tillförlitlig distans. **Kryptoautentiserad heartbeat över radio = "liveness/presens", inte "fysisk distans".** Sann säker närhetsmätning kräver UWB secure ranging (FiRa). [NCC Group](https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/) · [FiRa](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf)
- **Auth enligt NIST 800-63B AAL2** = två faktorer, minst en possession-baserad; FIDO2/WebAuthn (som vår PicoFIDO-badge) uppfyller det och är phishing-resistent. [NIST 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)
- **WebAuthn på en lokal SBC kräver en domän, inte IP-adress**: RP ID måste vara en domänsträng och WebAuthn kräver en säker (TLS) kontext — det måste mockas/lösas för lokal 127.0.0.1-testning. [web.dev](https://web.dev/articles/webauthn-rp-id)
- **Behörighet (authz) görs i noden med zonmodell**: NIST 800-82r3 / IEC 62443 least-privilege; Cub/LLM-agenten får aldrig kontrollplanet (datadiod-princip). [NIST 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)

---

## 2. Del A: Kan UNO Q 4GB köra TinyML + gatekeeper samtidigt?

### 2.1 Vad källorna säger om hårdvaran

- UNO Q är en **dual-arkitektur** ("one board, two brains"): en **QRB2210** (Qualcomm-applikationsprocessor) som kör Debian Linux, och en **STM32U585** (ST-säkerhets-MCU, Cortex-M33 @ 160 MHz, TrustZone, PSA Level 3 / SESIP3-certifierad) som kör Zephyr RTOS. De talar med varandra via **Bridge RPC**. [Arduino Docs](https://docs.arduino.cc/hardware/uno-q/) · [User Manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/)
- 4GB-varianten har **4 GB LPDDR4X RAM och 32 GB eMMC**. [Arduino Docs](https://docs.arduino.cc/hardware/uno-q/)
- QRB2210: fyra Cortex-A53-kärnor @ ~2 GHz, med AI-stöd. [Arduino Docs](https://docs.arduino.cc/hardware/uno-q/) · [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- Qualcomm beskriver en **"split processing"-design** där MPU:n (Linux) tar "AI inference, computer vision, media streaming, data analytics och Python-applikationer" medan MCU:n tar "deterministisk realtidsstyrning, tidskritisk I/O och låg-latens-drift". [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- STM32U585 har hårdvarukrypto (AES, PKA, HASH, TRNG), TrustZone-miljö (secure/non-secure-världar) och PSA Level 3 / SESIP3-certifiering — dvs. "bank-grade" säkerhetsegenskaper på MCU:n. [ST](https://www.st.com/en/microcontrollers-microprocessors/stm32u585ai.html) · [embedded.com](https://www.embedded.com/stm32u5-mcus-achieve-psa-certified-level-3-and-sesip-certifications/)

### 2.2 Vad källorna säger om prestanda (A53 + TinyML)

- **Isolation Forest på MCU (ESP32)**: tränas i 1,2–6,4 s och infererar i <16 ms med ~84 KB RAM. [MDPI Sensors](https://www.mdpi.com/1424-8220/23/4/2344)
- **Indikativa benchmarks på Raspberry Pi 3B+** (samma 4× Cortex-A53, men 1,4 GHz och 1 GB RAM — QRB2210 är 2 GHz och 4 GB): [samanvya.dev](https://samanvya.dev/blog/anomaly-detection-raspberry-pi)
  - Conv Autoencoder FP32 (12 MB): ~180 ms inferens, ~340 MB RAM
  - Conv Autoencoder int8/TFLite (3 MB): ~45 ms, ~95 MB RAM
  - Isolation Forest (sklearn, 2 MB): ~8 ms, ~60 MB RAM
  - Dense Autoencoder int8 (800 KB): ~12 ms, ~40 MB RAM
  - (källa är en blogg — **indikativ, inte primär**; siffrorna visar ändå att små modeller är triviala för A53)
- **A53-int8-varning**: på Cortex-A53 kan int8-kvantiserade TFLite-modeller bli *långsammare* än float32 eftersom A53 saknar dot-produkt-instruktioner (till skillnad från A55/A76 och nyare). Rekommendationen för A53 är float32 + XNNPACK. [Google AI-forum](https://discuss.ai.google.dev/t/int8-tflite-model-performs-worse-than-float32-model-on-arm-cortex-a53/90390/4)
- **Linux-realtid**: PREEMPT_RT ger determinism i tiotals µs; Red Hat rapporterar max-latens <15 µs och en screw-to-screw worst case (~6,7 ms) som aldrig överskreds ens med 50–70 % bakgrundslast. Men: Linux ger **mjuk** realtid, medan **hård** realtid (garanterade deadlines) görs på MCU/RTOS. [Red Hat](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge) · [docs.kernel.org](https://docs.kernel.org/core-api/real-time/)

### 2.3 Vår bedömning för UNO Q 4GB (resursbudget)

Gatekeeper-arbetet på Linux-sidan är **billigt**:
- FIDO2/WebAuthn-verifiering: publik-nyckel-krypto (ECDSA/ed25519) — millisekunder per verifiering, sparsamt med RAM. [Yubico](https://developers.yubico.com/Passkeys/Passkey_relying_party_implementation_guidance/)
- Heartbeat-dekryptering av LoRa-paket (AES) på QRB2210: trivialt (~kB-paket, ms-nivå). LoRa 868 har låg datatakt (<1 kbps praktiskt), så CPU-belastningen är minimal. [Semtech](https://www.semtech.com/uploads/technology/LoRa/theory-and-principle-of-advanced-ranging.pdf)
- Policy / regelutvärdering: millisekunder.

TinyML-arbetet:
- Klassisk/linjär ML (Isolation Forest, OCSVM) eller små autoencoders: **~8–45 ms inferens, 40–100 MB RAM**. Det är ingenting mot 4 GB.
- Även en "tung" CNN (SSD MobileNet V2-liknande) kör på ~0,6 s med ~150 MB footprint på liknande A53-hårdvara (TI AM62X) — körbart, men onödigt för vår nyttolast.

**Slutsats budget:** samtidig körning ger ingen resurskonflikt i normalfallet. Worst-case (inferens + heartbeat + verifiering samtidigt) kostar totalt <0,5 s CPU-burst och <200 MB RAM extra — 4 GB räcker med bred marginal.

### 2.4 MPU/MCU-partitionering och worst-case

- **Rekommendation:** allt **tidskritiskt + fail-safe** (heartbeat-klocka, låsstyrning via GPIO, oberoende watchdog) läggs på **STM32U585/Zephyr**. Allt **beräknings- och policy-tungt** (ML-inferens, FIDO2-verifiering, loggning, MQTT) läggs på **QRB2210/Linux**. [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- **Worst-case-scenariot är inte "Linux hänger"** — det hanteras av MCU-watchdog + fail-safe-lås. Worst case är att *Linux-sidan* blir trög (t.ex. minnespaginering, inferens-slowdown). Effekten blir fördröjd verifiering, inte osäkrad dörr. Detta är den viktigaste arkitekturpoängen: Linux kan vara långsam, MCU:n håller säkerheten. [Red Hat](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge) · [docs.kernel.org](https://docs.kernel.org/core-api/real-time/)
- **Honest caveat:** UNO Q är ingen kraftplattform — prestandan ligger i Raspberry Pi 3 / Pi Zero 2W-klassen. Tunga LLM/ViT-liknande modeller på noden är orealistiskt; små modeller är det rätta valet.

---

## 3. Del B: Best practice för heartbeat/proximity + auth + behörighet på en SBC

### 3.1 Authentication (vem är det?)

- **NIST SP 800-63B AAL2** kräver två distinkta faktorer, minst en possession-baserad, med godkända krypto. FIDO2/WebAuthn (kryptografiska nycklar på enheten) uppfyller AAL2 och är **phishing-resistent** (nyckeln är bunden till RP-domänen). [NIST 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) · [web.dev](https://web.dev/articles/webauthn-rp-id)
- **Vår PicoFIDO-badge** (ESP32-S3 + pico-fido2) = en possession-faktor (kryptografisk nyckel) + PIN/lås = en andra faktor. Det matchar AAL2. [Yubico RP-guide](https://developers.yubico.com/Passkeys/Passkey_relying_party_implementation_guidance/)
- **Viktig detalj för lokal SBC:** WebAuthn **RP ID måste vara en domänsträng** — IP-adresser är inte tillåtna. För en helt lokal testuppställning måste man antingen köra mot en lokal domän (t.ex. `gatekeeper.local` via mDNS/DNS) eller mocka origin-bindningen i en test-HDMI-enhet. [web.dev](https://web.dev/articles/webauthn-rp-id)

### 3.2 Proximity / heartbeat (är enheten faktiskt här?)

- **BLE-proximity är brutet som enda faktor:** NCC Group visar en **link-layer-reläattack** som fungerar även mot krypterade BLE-anslutningar; GATT-latensmätningar är inte en tillförlitlig försvarslinje. [NCC Group](https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/)
- **RSSI är inte distans:** BLE/LoRa-RSSI varierar med dB-nivåer och ger meterfel (upp till ~1,3 m fel redan vid 10 dBm variation). RSSI kan därför bara användas som grov närvaro, aldrig som säker distans. [FiRa whitepaper](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf)
- **Sann distansmätning = UWB secure ranging:** FiRa-konsortiet definierar UWB-baserad "secure ranging" med centimeters-precision, skyddad mot distansförkortning (distance shortening). Branschstandard (t.ex. bilnycklar, Apple/NXP-ekosystem). [FiRa whitepaper](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf)
- **Till och med UWB kan attackeras:** "Ghost Peak" (USENIX 2022) visar en distansreduktionsattack mot HRP-UWB i 4 % av fallen — även säker avståndsmätning behöver fler åtgärder (multi-measurement, STS, etc.). [Ghost Peak](https://www.usenix.org/conference/usenixsecurity22/presentation/ghost-peak)
- **LoRa SX1262 (vår hårdvara) kan INTE göra secure ranging:** Semtechs RTToF-avståndsmätning (LoRa Advanced Ranging) finns i **SX1280**-serien, inte SX1262. Vår LoRa-länk är en **kryptoautentiserad data-länk för heartbeat**, inte en distansmätare. [Semtech](https://www.semtech.com/uploads/technology/LoRa/theory-and-principle-of-advanced-ranging.pdf)
- **Best practice:** använd **kryptoautentiserad heartbeat** (nonce + MAC/tidsstämpel över LoRa 868 med AES) som **liveness/presens**-signal — "badgen svarade nyligen med giltiga nycklar", inte "badgen är 2 m bort". Kalla det `presence`, inte `proximity`.

### 3.3 Authorization (vad får enheten göra?)

- **Zon/konduit-modellen (IEC 62443 / NIST 800-82r3):** gatekeeper-noden är en egen zon; kommunikation in/ut går via kontrollerade konduiter. [Cisco/62443](https://www.cisco.com/c/en/us/products/collateral/security/isaiec-62443-3-3-wp.html) · [NIST 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- **Least privilege:** noden har *läsa* PLC-data (read-only) via OPC UA, och *inget* skrivkontroll mot PLC. [NIST 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- **Cub/LLM-agenten får aldrig kontrollplanet:** agenten är read-only-observatör; beslut och låsutlösning ligger i separata funktioner (datadiod-princip). [NIST 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- **Policy lokal och enkel:** auth (FIDO2-ok) + presence (färsk heartbeat) + policy (zontid, roll, nodstatus) → beslut. Policy-verifiering är billig och kan även ligga i MCU för redundans. [NIST 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)

### 3.4 Källan vs vår bedömning — sammanfattning

| Aspekt | Källan säger | Vår bedömning för SHALLOT |
|---|---|---|
| Proximity via BLE RSSI | Ej tillförlitlig, reläattacker [NCC](https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/) | Används ej som säkerhetsfaktor |
| Proximity via LoRa RSSI | Ej definierad som säker distans [Semtech](https://www.semtech.com/uploads/technology/LoRa/theory-and-principle-of-advanced-ranging.pdf) | Heartbeat = presence, inte proximity |
| Säker distans | UWB secure ranging (FiRa) [FiRa](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf) | Framtida hårdvara; mockas nu |
| Auth | AAL2, phishing-resistent [NIST](https://pages.nist.gov/800-63-3/sp800-63b.html) | FIDO2/WebAuthn = vår väg |
| Authz | Zoner + least privilege [NIST 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) | Implementeras i noden |

---

## 4. Rekommendation för SHALLOT/UNO Q (konkret arkitektur)

### 4.1 Arbetsdelning

- **STM32U585 (Zephyr, MCU):** heartbeat-klocka och LoRa-pakethantering, fail-safe-låsstyrning via GPIO, oberoende watchdog, TrustZone-skyddad nyckellagring (badge-/radio-nycklar). Detta är nodens "säkerhetskärna" — certifierad till PSA Level 3/SESIP3, hård realtid. [ST](https://www.st.com/en/microcontrollers-microprocessors/stm32u585ai.html) · [embedded.com](https://www.embedded.com/stm32u5-mcus-achieve-psa-certified-level-3-and-sesip-certifications/)
- **QRB2210 (Debian, Linux):** TinyML-inferens (anomalidetektering på PLC-data), FIDO2/WebAuthn-RP (lokal RP med domänbaserad RP ID), policy-/beslutslogik, loggning + MQTT uppåt, Docker. En av fyra kärnor räcker för inferens.
- **Bridge RPC** är gränssnittet: MCU:n exponerar "heartbeat-status + badge-id" och "lock-command" som säkra RPC; Linux-sidan fattar policybeslut och MCU:n utför. [Arduino Docs](https://docs.arduino.cc/hardware/uno-q/)

### 4.2 Ärlig modellstorlek (TinyML)

- **Rekommendation: Isolation Forest** (~2 MB, ~8 ms inferens, ~60 MB RAM) eller **liten int8-autoencoder** (~800 KB, ~12 ms) på float32/XNNPACK. Båda ryms med bred marginal; ingen risk att de konkurrerar med gatekeeper-arbetet. [samanvya.dev](https://samanvya.dev/blog/anomaly-detection-raspberry-pi) · [MDPI Sensors](https://www.mdpi.com/1424-8220/23/4/2344) · [Google AI-forum](https://discuss.ai.google.dev/t/int8-tflite-model-performs-worse-than-float32-model-on-arm-cortex-a53/90390/4)
- **Undvik:** tunga CNN/transformer-modeller (>100 MB) — onödig komplexitet och risk för tröghet på A53.
- Verifiera prestanda i testmiljön (cProfile + `/usr/bin/time`) innan arkitektur fastställs.

### 4.3 Vad mockas / verifieras

- **Mockas nu:** UWB secure ranging (ingen hårdvara) — dokumentera `presence` (heartbeat) som ersättning, samt ev. framtida uppgradering (t.ex. DWM3000 UWB-modul på SPI). [FiRa](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf)
- **Mockas:** helt lokal WebAuthn (RP ID-domän), TLS-certifikat och MQTT-broker uppåt.
- **Verifieras:** Bridge RPC-pålitlighet, LoRa 868-paketförlust i testmiljö, STM32U585-watchdog-beteende, Linux PREEMPT_RT-latens (om tillgänglig i UNO Q-avbilden). [Red Hat](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge)

---

## 5. Slutsats

- **Del A (resursbudget):** Ja — UNO Q 4GB kan samtidigt köra TinyML och gatekeeper, *om* tidskritisk/fail-safe-logik ligger på STM32U585 och inferens/policy på QRB2210. Modellerna behöver vara små (klassisk ML / liten autoencoder); Linux-sidan tål att bli trög utan att säkerheten bryts. [Arduino Docs](https://docs.arduino.cc/hardware/uno-q/) · [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q) · [Red Hat](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge)
- **Del B (heartbeat + auth):** Kryptoautentiserad heartbeat (LoRa 868, AES, nonce) = presence. FIDO2/WebAuthn = auth (AAL2). Policy + zoner = authz. UWB secure ranging = den enda "äkta" distansmätningen, men kräver ny hårdvara och mockas. [NCC Group](https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/) · [NIST](https://pages.nist.gov/800-63-3/sp800-63b.html) · [FiRa](https://www.firaconsortium.org/sites/default/files/2022-08/FIRA-Whitepaper-UWB-Secure-Ranging-August-2022.pdf)
- **Designändringar som följer:** (1) LoRa SX1262 är *inte* en distansmätare — terminologi blir `presence`, inte `proximity`; (2) fail-safe-lås + watchdog på STM32U585, inte Linux; (3) WebAuthn kräver domänbaserad RP ID (lokal domän eller mock); (4) Cub/agent förblir read-only — inga skrivbehörigheter.
