# Research Report: SBC-Edge för realtids-PLC/sensordataflöde

**Issue:** Forskning för SHALLOT/Cub edge-arkitektur (UNO Q 4GB-noden)
**Author:** AI Agent
**Date:** 2026-08-15
**Status:** Completed

---

## 0. Primära källor (läslista)

1. **OPC UA** — OPC Foundation, specifikationsserien IEC 62541. [OPC UA Online Reference](https://reference.opcfoundation.org/) · [UA Part 1: Overview and Concepts](https://profiles.opcfoundation.org/document/1)
2. **Modbus** — Modbus Organization, *MODBUS Application Protocol Spec V1.1b3*. [modbus.org](https://www.modbus.org/modbus-specifications) · [Spec PDF](http://www.modbus.org/file/secure/modbusprotocolspecification.pdf)
3. **Sparkplug B (MQTT)** — Eclipse Foundation, Sparkplug-specifikationen. [Sparkplug 3.0 spec](https://sparkplug.eclipse.org/specification/) · [Sparkplug 2.2 PDF](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf) · [Eclipse-projektsidan](https://projects.eclipse.org/projects/iot.sparkplug)
4. **OPC DA (Classic)** — OPC Foundation, Windows/COM/DCOM-baserad. [Software Toolbox: What is OPC DA](https://softwaretoolbox.com/resources/what-is-opc-da)
5. **NIST SP 800-82r3** — *Guide to Operational Technology (OT) Security* (2023). [CSRC-sida](https://csrc.nist.gov/pubs/sp/800/82/r3/final) · [PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
6. **CISA/ICS-CERT** — *Cybersecurity Best Practices for Industrial Control Systems* (rekommendationer om datadiod, DMZ, segmentering). [PDF](https://www.cisa.gov/sites/default/files/publications/Cybersecurity_Best_Practices_for_Industrial_Control_Systems.pdf) · [ICS Recommended Practices](https://www.cisa.gov/resources-tools/resources/ics-recommended-practices)
7. **ISA-95 / IEC 62264** — ISA:s officiella standardsida. [isa.org](https://www.isa.org/standards-and-publications/isa-standards/isa-95-standard)
8. **IEC 62443** — ISA/IEC 62443-serien; zon/konduit-arkitektur och FR1–FR7. [IEC SyC-sida](https://syc-se.iec.ch/deliveries/cybersecurity-guidelines/security-standards-and-best-practices/iec-62443/) · [Cisco: ISA/IEC-62443-3-3](https://www.cisco.com/c/en/us/products/collateral/security/isaiec-62443-3-3-wp.html)
9. **PREEMPT_RT** — Linux-kärndokumentationen + leverantörsdata. [docs.kernel.org real-time](https://docs.kernel.org/core-api/real-time/) · [Red Hat: determinism i industriell edge](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge) · [Ubuntu Real-time docs](https://ubuntu.com/real-time/docs/) · [NXP Real-Time Edge release notes](https://www.nxp.com/docs/en/release-note/RN00161.pdf)
10. **Arduino UNO Q 4GB** — Arduino/Qualcomm primärdokumentation. [Arduino Docs UNO Q](https://docs.arduino.cc/hardware/uno-q/) · [UNO Q User Manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/) · [Qualcomm-sidan för UNO Q](https://www.qualcomm.com/developer/hardware/arduino-uno-q) · [Zephyr: UNO Q-board](https://docs.zephyrproject.org/latest/boards/arduino/uno_q/doc/index.html)
11. **TinyML / edge-AI** — granskad litteratur + Arduino AI-verktyg. [MDPI Sensors: Isolation Forest på MCU](https://www.mdpi.com/1424-8220/23/4/2344) · [Springer/PMC: lättvikts edge-anomalidetektering](https://pmc.ncbi.nlm.nih.gov/articles/PMC12610206/) · [Arduino App Lab AI-modeller](https://docs.arduino.cc/software/app-lab/tutorials/ai-models/) · [Arduino ML-guide](https://docs.arduino.cc/tutorials/nano-33-ble-sense/get-started-with-machine-learning)

---

## 1. Kort sammanfattning

- **De facto-standard för modern OT-datainsamling är OPC UA** (IEC 62541, OPC Foundation); för gamla/legacy-PLC är Modbus/TCP (och OPC DA) fortfarande dominerande eftersom de kan pollas utan inbyggd säkerhet. [OPC UA](https://reference.opcfoundation.org/) · [Modbus](http://www.modbus.org/file/secure/modbusprotocolspecification.pdf)
- **MQTT + Sparkplug B (Eclipse) är standarden för IIoT-edge-uppkoppling** och är uttryckligen designad för att en "Edge of Network"-nod (precis vår SBC) ska aggregera PLC-/sensordata och publicera dem uppåt. [Sparkplug 2.2](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf)
- **Purdue-modellen + IEC 62443-zoner/konduiter är referensarkitekturen**; edge-noder sitter typiskt i nivå 2–3 (övervakning) och NIST/CISA bekräftar att **datadiod / unidirektional gateway vid OT/IT-gränsen är standardpraxis** för skrivskyddad övervakning. [NIST SP 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) · [CISA](https://www.cisa.gov/sites/default/files/publications/Cybersecurity_Best_Practices_for_Industrial_Control_Systems.pdf)
- **En Linux-SBC kan hantera "mjuk" realtid** (PREEMPT_RT ger determinism i tiotals µs), men **hård realtid (garanterade svarstider) görs av MCU/RTOS** — precis UNO Q:s dual-brain-design: QRB2210 (Linux) + STM32U585 (Zephyr). [Red Hat](https://www.redhat.com/en/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge) · [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/)
- **Klassisk/linjär ML och TinyML ryms med bred marginal på en Cortex-A53-SBC**: Isolation Forest tränas och körs till och med på en MCU (ESP32, 80 KB RAM) på millisekunder. [MDPI Sensors](https://www.mdpi.com/1424-8220/23/4/2344)
- **Vår read-only-modell är inte bara accepterad — den uppmuntras**: NIST 800-82r3 anger att "lower privileges include read access, higher privileges include write access" och IEC 62443 FR2/FR5 bygger på least privilege + begränsade dataflöden. [NIST](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) · [Cisco/62443](https://www.cisco.com/c/en/us/products/collateral/security/isaiec-62443-3-3-wp.html)

---

## 2. Hur realtids-PLC/sensordata samlas in på edge (protokoll, källor)

### 2.1 OPC UA — standarden för modern OT
- Källan säger: OPC UA är en plattforms-oberoende standard (IEC 62541) som "är tillämplig på komponenter i alla industriella domäner, såsom industriella sensorer och ställdon, styrsystem, MES och ERP, inklusive IIoT, M2M, Industrie 4.0". Specen definierar informationsmodell, meddelandemodell, kommunikationsmodell och konformansmodell. [UA Part 1](https://profiles.opcfoundation.org/document/1)
- Källan säger: OPC UA har inbyggd autentisering, kryptering och meddelandeintegritet (X.509-certifikat, 256-bitars kryptering), och stödjer både klient/server och Publish-Subscribe. [Embien-guide](https://www.embien.com/industrial-insights/a-comprehensive-guide-to-the-opc-ua-standard) · [Software Toolbox jämförelse](https://softwaretoolbox.com/resources/what-is-opc-da)
- Källan säger: moderna PLC:er (Siemens S7-1500, Beckhoff TwinCAT, Allen-Bradley med flera) har OPC UA-servrar inbyggda. [FlowFuse](https://flowfuse.com/blog/2025/07/reading-and-writing-plc-data-using-opc-ua)
- **Vår bedömning:** OPC UA är förstahandsvalet för läsning från moderna PLC:er. Kritiskt för oss: OPC UA kan konfigureras **read-only** per användare/nod (skrivbehörighet separeras), och TLS gör kommunikationen brandväggsvänlig över en port — bra för Purdue-gränsen. [Software Toolbox: DCOM vs UA](https://softwaretoolbox.com/resources/what-is-activex)

### 2.2 Modbus/TCP — arbetshästen för äldre PLC:er
- Källan säger: Modbus är ett klient/server-protokoll på applikationslagret, med en enkel registermodell (coils, input registers, holding registers) och funktionskoder. Det var designat för enkelhet, inte säkerhet. [Modbus-spec V1.1b3](http://www.modbus.org/file/secure/modbusprotocolspecification.pdf)
- Källan säger: Modbus/TCP körs på TCP-port 502 och har inga inbyggda säkerhetsmekanismer; en separat "Modbus Security Protocol" (TLS-inkapsling) finns men kräver stöd i båda ändar. [Modbus Security Protocol](https://www.modbus.org/file/secure/modbussecurityprotocol.pdf) · [ProSoft intro](https://www.prosoft-technology.com/kb/assets/intro_modbustcp.pdf)
- **Vår bedömning:** För befintliga PLC-utbud i en testmiljö är Modbus/TCP det mest sannolika inläsningsprotokollet (simple, dokumenterat, stöds av alla OPC UA-server/gateway-verktyg). Säkerhet måste då ligga i nätverkssegmentet, inte i protokollet — vilket stärker vårt dataflödesbeslut.

### 2.3 MQTT + Sparkplug B — edge-nodens "talspråk" uppåt
- Källan säger: Sparkplug (Eclipse) definierar ett MQTT-topic-namnområde, ett typat protobuf-payload och "birth/death-certifikat" för tillståndshantering, optimerat för SCADA/IIoT. En **Edge of Network (EoN)-nod** "tillhandahåller gatewayfunktioner för sensorer/enheter som inte själva implementerar Sparkplug" — dvs. precis vår SBC-roll. [Sparkplug 2.2](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf) · [Eclipse-projekt](https://projects.eclipse.org/projects/iot.sparkplug)
- Källan säger: "the existing population of 100's of millions of smart devices need to be 'asked' if something has changed using poll/response protocols … the solution being employed today is to place this capability in small embedded devices closer to the data producers themselves." (100-tals miljoner enheter pollas; lösningen är små edge-enheter nära datakällan.) [Sparkplug 2.2](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf)
- Källan säger: endast den utsedda **Primary Application** får publicera kommandon (NCMD/DCMD); andra noder kan köra "i a pure monitoring mode" (ren övervakning). [Sparkplug 2.2 §3.5](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf) · [Opto 22](https://www.opto22.com/articles/industrial-strength-mqtt-sparkplug-b)
- **Vår bedömning:** Ett naturligt val för vår edge-nod är: läs via OPC UA/Modbus från PLC → analysera lokalt (Tier 0) → publicera endast övervakningsdata/NDATA uppåt via Sparkplug. Sparkplugs "monitoring mode" matchar vår noll-behörighetsprincip.

### 2.4 OPC DA (Classic) — legacy
- Källan säger: OPC DA bygger på Microsoft COM/DCOM, är Windows-only, kräver DCOM-brandväggskonfiguration (TCP 135 + dynamiska portar) och har ingen plattforms-oberoende säkerhet. OPC Foundation rekommenderar migration till OPC UA för fjärrkommunikation. [Software Toolbox](https://softwaretoolbox.com/resources/what-is-opc-da) · [Software Toolbox: ActiveX/DCOM](https://softwaretoolbox.com/resources/what-is-activex)
- **Vår bedömning:** OPC DA är inte relevant för vår Debian-baserade SBC (kan inte ens köras på Linux). Om en äldre OPC DA-källa finns, överbryggas den med en UA-gateway någon annanstans — inte i vår nod.

---

## 3. Standardarkitektur för dataflödet (Purdue/IEC 62443, edge-nivå, datadiod)

### 3.1 Purdue-modellen och ISA-95/IEC 62264-nivåerna
- Källan säger: NIST SP 800-82r3 anger Purdue-modellen, ISA-95-nivåerna och tre-nivåernas IIoT-arkitektur som accepterade sätt att segmentera OT-nät. [NIST SP 800-82r3, kap. om nätverkssegmentering](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- Källan säger: ISA-95 (internationellt IEC 62264) definierar en funktionell hierarki: Nivå 0 (process), Nivå 1 (sensor/ställdon), Nivå 2 (PLC/SCADA — processkontroll), Nivå 3 (MES/operations), Nivå 4 (ERP). [ISA-95](https://www.isa.org/standards-and-publications/isa-standards/isa-95-standard)
- **Vår bedömning:** Vår edge-nod hör hemma i **gränsen Nivå 2–3** (övervakning/insamling): den läser från Nivå 1-enheter (PLC) men ska inte placeras som om den styr Nivå 1. Purdue/ISA-95 ger oss språket att dokumentera detta.

### 3.2 IEC 62443 — zoner, konduiter och var edge-noden sitter
- Källan säger: IEC 62443 bygger på zoner och konduiter (segmentering av IACS), med sju Foundational Requirements (FR1–FR7) och säkerhetsnivåer SL1–SL4. Nätverkssegmentering används för att "minska exponeringen av styrsystemet och begränsa spridningen av attacker". [IEC SyC](https://syc-se.iec.ch/deliveries/cybersecurity-guidelines/security-standards-and-best-practices/iec-62443/) · [Cisco/62443-3-3](https://www.cisco.com/c/en/us/products/collateral/security/isaiec-62443-3-3-wp.html)
- Källan säger: en konduit är inte en kabel utan en "policy-förstärkt kanal"; rekommenderad praxis är att datadelning mellan zon med hög säkerhetsnivå (t.ex. säkerhetssystem) och annan zon sker via **unidirektional gateway eller skrivskyddad OPC UA-anslutning**, aldrig en tvåvägs-anslutning som tillåter skrivning. [TechWem: 62443-praktikguide](https://techwem.com/iec-62443-zones-and-conduits-a-practical-implementation-guide/) *(sekundärkälla, men en direkt tolkning av 62443-3-3)*
- **Vår bedömning:** Vår nod bör vara en egen zon (eller en "zone of one") med egen konduit ut ur produktionszonen. Konduiten ut är datadioden/read-only-proxyn. Att noden saknar styrkanal gör att den kan ges lägre påverkansyta på PLC:erna än en SCADA-server.

### 3.3 Datadiod / unidirektional gateway — standardpraxis för övervakning
- Källan säger: "A **data diode** is a network appliance or device that allows data to travel only in one direction … a common use case is placing a data diode at the boundary between the operational network and the enterprise network … preventing a potential avenue of cyber attack." [NIST SP 800-82r3, ordlista + bilaga E.1.2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- Källan säger: NIST listar "unidirectional gateways/data-diodes" som nätverksenheter som "kan användas för att implementera nätverkssegmentering och isolering", tillsammans med brandväggar. [NIST SP 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- Källan säger (CISA/ICS-CERT): "**Use one-way communication diodes to prevent external access, whenever possible**" och "Set up demilitarized zones (DMZ) … as an intermediary". [CISA Cybersecurity Best Practices for ICS](https://www.cisa.gov/sites/default/files/publications/Cybersecurity_Best_Practices_for_Industrial_Control_Systems.pdf)
- **Vår bedömning:** Vår befintliga designbeslut (enkelriktat flöde / read-only proxy vid Purdue-gränsen, noll kontrollbehörigheter) matchar direkt NIST:s datadiod-användningsfall och CISA:s rekommendation. Detta är **standardpraxis**, inte något udda.

---

## 4. Kan en Linux-SBC (UNO Q 4GB) klara realtids-edge? Gränser och var MCU/RTOS tar över

### 4.1 Vad Linux realtid faktiskt kan
- Källan säger: PREEMPT_RT gör Linux "till en fungerande plattform för mjuk och fast realtid"; det mesta av PREEMPT_RT är sedan kärna 6.x inbyggt i mainline. För "sub-10 µs garanterad latens eller hård realtidscertifiering" behövs en dedikerad RTOS-coprocessor (eller Xenomai/RTAI). [docs.kernel.org](https://docs.kernel.org/core-api/real-time/) · [Proteanos-guide](https://proteanos.com/doc/real-time-linux-preempt-rt-latency-2026/)
- Källan säger (Red Hat, mätdata på x86): med realtidskärnan uppmättes maxlatens under 15 µs, determinism i "low tens of microseconds" även under tung last. [Red Hat](https://www.redhat.com/blog/deterministic-performance-red-hat-enterprise-linux-industrial-edge)
- Källan säger: Ubuntu levererar Real-time Ubuntu med PREEMPT_RT-kärnan för determinism och lägre latens i industri-, telekom- och robotapplikationer. [Ubuntu](https://ubuntu.com/real-time/docs/)
- **Vår bedömning:** För vårt fall (läsa sensor/PLC-värden med sekund-till-millisekund-intervall, köra klassisk ML och publicera resultat) räcker standard- eller PREEMPT_RT-Linux med god marginal. "Realtid" vi behöver är *best-effort låg latens*, inte garanterad loopstyrning.

### 4.2 UNO Q:s dual-brain-design (bekräftad mot primärkälla)
- Källan säger: Arduino UNO Q kombinerar **Qualcomm Dragonwing QRB2210** (quad Arm Cortex-A53 @ 2,0 GHz, Adreno GPU, dubbla ISP:er) som kör full Debian Linux, med en **STM32U585** (Arm Cortex-M33 @ 160 MHz, 2 MB flash, 786 KB SRAM) som kör Arduino-skisser över **Zephyr OS**. [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/) · [Zephyr: UNO Q](https://docs.zephyrproject.org/latest/boards/arduino/uno_q/doc/index.html)
- Källan säger: 4GB-varianten har 4 GB LPDDR4X och 32 GB eMMC. [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/) · [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- Källan säger (Qualcomm): "The MPU handles high-level computing tasks like AI inference, media control and connectivity, while the MCU ensures **real-time control** for motors, sensors, and low-latency signal processing." [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- Källan säger (Arduino): UNO Q blandar "high-performance computing med **deterministic real-time control**" — MCU-sidan är den deterministiska. [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/)
- **Vår bedömning:** Detta bekräftar exakt vår tänkta fördelning: **Linux-sidan (A53) = datainsamling, ML-analys, kommunikation uppåt; STM32U585-sidan = tidskritiskt I/O** (t.ex. snabb sampling/pulsräkning, exakta tidsstämplar, låsning/status via GPIO, lokal buffring vid nätverksavbrott). MCU:n kan också vara den enda enhet som har hårdvaru-åtkomst till "aktiverings-pins" om sådana någonsin behövs — men enligt vår arkitektur ska den *inte* få kontrollera PLC:en.

### 4.3 Heterogen MCU+MPU som industrimönster
- Källan säger: NXP:s Real-Time Edge-programvara gör just detta — Preempt-RT Linux på Cortex-A-kärnor, RTOS/bare-metal på Cortex-M-kärnor med "deterministic behavior … suitable for deterministic real-time applications", med ramverk för interkärnkommunikation. [NXP RN00161](https://www.nxp.com/docs/en/release-note/RN00161.pdf)
- **Vår bedömning:** "Linux + RTOS på delad hårdvara" är ett etablerat industrimönster (även om UNO Q använder två separata kretsar i stället för delad SoC). Vi bör utnyttja MCU:n för allt som behöver garanterade tider, och aldrig förvänta oss det av Docker/Linux-lagret.

---

## 5. Edge AI för avvikelsedetektering på sensordata

### 5.1 Klassisk ML ryms på mycket svagare hårdvara
- Källan säger: Ett system på en ESP32-MCU (80 KB RAM) tränar en **Isolation Forest** på enheten på **1,2–6,4 s** och detekterar en avvikelse på **mindre än 16 ms** (50 träd, ensembleregression) — helt osupervided (utan etiketter), för submersibla pumpar i industriell miljö. [MDPI Sensors 2023](https://www.mdpi.com/1424-8220/23/4/2344)
- Källan säger: en lättviktsram med **klassisk signalbehandling (Fourier/vågextraktion) + ML på edge** nådde F1 ≈ 0,94 (grund neural) och F1 ≈ 0,92 med en kvantiserad TinyML-modell som minns tre gånger mindre och drar 60 % mindre energi; decision trees gav sub-millisekund-latens. [Springer/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12610206/)
- **Vår bedömning:** Vår Tier 0-plan (klassisk ML: statistiska metoder, isolation forest, trösklar) är konservativ och körs med bred marginal på en fyrkärnig A53. Ingen LLM krävs; detta utesluter även behovet av att sända rådata uppåt för analys.

### 5.2 Verktygskedjor för AI på UNO Q
- Källan säger: Arduino App Lab integrerar Python, Arduino-skisser och AI-modeller i en miljö och stödjer att träna (t.ex. i Edge Impulse) och distribuera modeller som MobileNetV2 SSD optimerade för UNO Q. [Arduino App Lab AI-modeller](https://docs.arduino.cc/software/app-lab/tutorials/ai-models/) · [Arduino ML-guide](https://docs.arduino.cc/tutorials/nano-33-ble-sense/get-started-with-machine-learning)
- Källan säger: QRB2210 är marknadsförd för on-device-AI (GPU, ISP:er, fyrkärna 2 GHz). [Qualcomm](https://www.qualcomm.com/developer/hardware/arduino-uno-q)
- **Vår bedömning:** För klassisk ML behöver vi ingen tung AI-stack — scikit-learn-liknande modeller körs direkt i Python på Debian; App Lab/Edge Impulse blir relevant först om vi senare vill köra en TinyML-modell på MCU-sidan (t.ex. vibreringsklassificering i STM32:an).

### 5.3 Vad som passar på edge vs. vad som inte gör det
- Källan säger: TinyML-begreppet definieras ofta som ML på en MCU med kraftbudget < 1 mW, med hårda minnes- och energibegränsningar. [MDPI Sensors 2023](https://www.mdpi.com/1424-8220/23/4/2344)
- **Vår bedömning:** Vår SBC (4 GB RAM, watt-klass) är *flera storleksordningar* kraftfullare än TinyML-definitionen — så "ryms på SBC" är trivialt sant för klassisk ML. Det intressanta är att även den mycket enklare MCU:n klarar det, vilket stärker vårt Tier 0-koncept (körs även om Linux-sidan står still).

---

## 6. Vad detta betyder för SHALLOT/Cub (tillämpning + konsekvenser för vår arkitektur)

### 6.1 Protokollval
- **Primärt: OPC UA (read-only klient)** mot moderna PLC:er — inbyggd säkerhet, plattformsoberoende (Debian), skrivbehörigheter kan nekas per nod. [OPC UA](https://reference.opcfoundation.org/)
- **Fallback för legacy: Modbus/TCP** via UA-gateway eller direkt klient — men aldrig från vår nod med skrivrättigheter; vi läser bara holding/input-registers (funktion 03/04). [Modbus-spec](http://www.modbus.org/file/secure/modbusprotocolspecification.pdf)
- **Uppåt: MQTT + Sparkplug B** med vår nod i **ren övervakningsroll** (ingen NCMD/DCMD-publicering, inga skrivbehörigheter på PLC-sidan). [Sparkplug 2.2](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf)
- **Undvik: OPC DA** — kan inte köras på Linux, och DCOM är en säkerhetsrisk. [Software Toolbox](https://softwaretoolbox.com/resources/what-is-opc-da)

### 6.2 Nodens placering i arkitekturen
- Vår nod = en **egen IEC 62443-zon** (lågt förtroende, ingen styrförmåga) vars enda väg ut är en **datadiod/read-only-proxy** i Purdue-nivå 3.5 (DMZ). Det är exakt NIST:s data diode-användningsfall och CISA:s rekommendation. [NIST SP 800-82r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) · [CISA](https://www.cisa.gov/sites/default/files/publications/Cybersecurity_Best_Practices_for_Industrial_Control_Systems.pdf)
- PLC:er står i Nivå 1-zonen; SCADA/övervakning i Nivå 2–3. Vår nod hör hemma på gränsen mot Nivå 3, inte som ytterligare en Nivå 1-aktör.

### 6.3 Realtid: MCU-sidan tar över det tidskritiska
- Debian/Linux (Docker) = datainsamling, klassisk ML (Tier 0), loggning, publicering. [Ubuntu/Red Hat determinism](https://ubuntu.com/real-time/docs/)
- STM32U585 (Zephyr) = tidskritiskt I/O: snabb sampling, exakta tidsstämplar, lokal buffring, fysiska status-/lås-signaler — med garanterad respons. [Arduino UNO Q](https://docs.arduino.cc/hardware/uno-q/) · [Zephyr](https://docs.zephyrproject.org/latest/boards/arduino/uno_q/doc/index.html)
- Ingen PLC-styrning från någon av sidorna. Om ett framtida behov av aktivering skulle uppstå, görs det av PLC:n själv (människa/tillåtet system), aldrig av vår nod.

### 6.4 Least privilege och read-only är standardkrav, inte val
- Källan säger: NIST 800-82r3 kräver att OT-privilegier begränsas till det minsta som behövs, och anger uttryckligen att privilegiemodeller "may be tailored to enforce integrity and availability (e.g., lower privileges include read access, and higher privileges include write access)". [NIST SP 800-82r3, AC-6 + CM-7](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- Källan säger: IEC 62443-3-3:s FR2 (Use Control) = least privilege och RBAC; FR5 (Restricted Data Flow) = begränsa kommunikation mellan komponenter; SR 1.4–1.6 täcker least privilege, kontohantering och RBAC. [Cisco/62443-3-3](https://www.cisco.com/c/en/us/products/collateral/security/isaiec-62443-3-3-wp.html) · [IEC SyC](https://syc-se.iec.ch/deliveries/cybersecurity-guidelines/security-standards-and-best-practices/iec-62443/)
- **Vår bedömning:** "Noll kontrollbehörigheter för agenten" + datadiod = direkt efterlevnad av AC-6/CM-7 (NIST) och FR2/FR5 (62443). Detta gör arkitekturen **revisionsvänlig** och argumentet "vi följer 62443" hållbart.

### 6.5 Konsekvenser för SHALLOT/Cub specifikt
- **Cub (LLM-agenten)** får aldrig få en väg till PLC-skrivning. Även om den komprometteras helt, finns ingen kanal: dataflödet är fysiskt/logiskt enkelriktat vid gränsen, och nodens OPC UA-klient är autentiserad med en roll som bara har read. (NIST AC-6 read/write-modell + datadiod.) [NIST](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf)
- **SHALLOT (FIDO2-åtkomst)** är en separat mekanism på annan hårdvara (PicoFIDO/Pico 2 W); edge-noden ska *inte* implementera FIDO2-verifiering av styrsystem — den övervakar bara. Håll dem åtskilda i olika zoner.
- **Tier 0 (klassisk ML)** kan köra helt lokalt och offline; det gör systemet robust även om upplänken bryts — vilket NIST 800-82r3 också uppmuntrar (graceful degradation).
- **Dokumentera** noden som "monitor-only edge node, Zone …", med konduit som endast tillåter publicering av övervaknings-/audit-data.

---

## 7. Öppna frågor / nästa steg

- Verifiera i praktiken att UNO Q:s Debian-image stödjer PREEMPT_RT-kärna (annars: standardkärna + sched_deadline/schlecht för våra tidsbehov). [Ubuntu RT](https://ubuntu.com/real-time/docs/)
- Välj konkret datadiod-alternativ för prototypen: fysisk diod, eller "read-only-proxy" (enkelriktad MQTT-broker med publicerings-ACL som blockerar alla subscribe-skrivningar). [Sparkplug 2.2 §3.7](https://sparkplug.eclipse.org/specification/version/2.2/documents/sparkplug-specification-2.2.pdf)
- Ta beslut om OPC UA-server- eller gateway-lager för test-PLC:erna (t.ex. open62541) och om Modbus-inläsning behövs för den faktiska testutrustningen.
