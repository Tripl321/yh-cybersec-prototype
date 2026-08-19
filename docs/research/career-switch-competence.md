# Career-switch: vad arbetsgivare vill se — och vad SHALLOT/Cub visar

> Forskningsnota för YH-slutprojektet (SHALLOT + Cub). Fråga: vad letar arbetsgivare efter hos en
> karriärbytare med entry-level-ambitioner (SOC-analytiker / junior säkerhetsingenjör / säkerhetsanalytiker),
> och hjälper det här projektet dit? Alla påståenden om arbetsmarknaden är källhänvisade; "vår bedömning"
> är analys, inte fakta.
>
> Jargong-förklaringar görs första gången begreppet dyker upp.
>
> Sammanställd: 2026-08-15. Läs gärna [README.md](../../README.md) och [ADR 0006](../adr/0006-cub-agent-inference-architecture.md) parallellt.

---

## 1. Kort sammanfattning

- **Satsa på "bevis genom handling", inte titlar.** Rekryterare värderar praktisk erfarenhet och
  hands-on-projekt högre än betyg; 90 % av säkerhetscheferna säger att de skulle anställa någon med
  bara IT-arbetslivserfarenhet, medan bara 81 % accepterar någon med bara utbildning (ISC2 2025).
  Ett fungerande GitHub-projekt med blogginlägg är ett dokumenterat sätt att visa det (SANS).
- **Topp-3 på "vad vi värderar" är inte tekniska:** teamwork, problemlösning och analytiskt tänkande
  (ISC2 2025). Ett projekt som visar *beslut, avvägningar och tydlig kommunikation* är lika viktigt
  som kodkvantitet.
- **Entry-level-arbete = dokumentation, larmhantering, rapportering och fysisk åtkomstkontroll**
  (ISC2 2025). Projektet träffar just dessa uppgifter — SHALLOT *är* fysisk åtkomstkontroll och
  Cub hanterar larm/logg med spårbar dokumentation (provenanslogg).
- **Autentisering/identitet (IAM) och säker AI är två av de hetaste kompetenserna just nu.**
  AI är den vanligaste kompetensbristen enligt ISC2:s globala undersökning (41 %), och AI/ML nämns
  i allt fler säkerhetsannonser. Cub:s egress-verifiering och prompt-injection-tester är en
  *differentierande* vinkel som få YH-studenter kan visa.
- **Svenska arbetsgivare har rekryteringssvårigheter:** Arbetsförmedlingens prognos (2025) klassar
  IT-säkerhetsspecialister som yrke med "mycket liten konkurrens om jobben" — kandidatens marknad.
- **Vår bedömning: projektet är på rätt spår men för internt.** Det som saknas är inte kompetens utan
  *förpackning*: en offentlig, icke-teknisk berättelse som kopplar arbetet till konkreta jobbkrav,
  en demovideo och 1–2 blogginlägg.
- **En instegscertifiering (t.ex. CompTIA Security+) har stor utväxling** — 89 % av rekryterarna
  överväger kandidater med entry-level-cert, och certet passerar ofta automatiska såll (ATS, se nedan).
- **Konkreta luckor (rankat senare i §4):** (1) offentlig portfolio-narrativ, (2) demovideo +
  reproducerbart demo-flöde inkl. Cub, (3) "Säkerhet för AI"-writeup, (4) mini-SOC-artefakt
  (logganalys + triage + rapport), (5) användbarhetstest med riktiga personer.

---

## 2. Vad arbetsgivare söker vid entry-level

### 2.1 Arbetsmarknaden: stor efterfrågan, men ingången kräver bevis

- **CyberSeek** (NIST + Lightcast + CompTIA, baserat på verkliga jobbannonser): drygt **514 000**
  öppna cybersäkerhetstjänster i USA på 12 månader (maj 2024–april 2025), +12 % jämfört med året
  innan, och "skills-based hiring continues to gain momentum". Som nytt mått: **~10 % av annonserna**
  nämner AI-som-krav.
  <https://www.comptia.org/en/about-us/news/press-releases/CyberSeek-expands-cybersecurity-workforce-data-coverage-and-enhances-user-experience/>
  <https://www.cyberseek.org/>
- **ISC2:s globala undersökning (2025):** 4,8 miljoner obemannade cybersäkerhetsroller globalt,
  och de största kompetensluckorna är **AI (41 %)**, molnsäkerhet (36 %), riskbedömning (29 %),
  applikationssäkerhet (28 %) och GRC (27 %).
  <https://digital-skills-jobs.europa.eu/en/latest/opinions/skills-based-hiring-europes-best-defence-meeting-cybersecurity-skill-needs>
- **Varning — "entry-level-paradoxen":** arbetsgivare vill ha bevis att du kan jobba självständigt
  snabbt. ISC2 rapporterar att många entry-level-annonser listar orimliga krav (t.ex. CISSP eller
  5 års erfarenhet), och att 56 % av arbetsgivarna räknar med 4–9 månaders upplärning av ny personal.
  Din uppgift är att *förkorta den tiden i deras ögon* — med bevis, inte löften.
  <https://www.prnewswire.com/news-releases/isc2-research-reveals-organizations-must-amend-early-career-hiring-practices-to-strengthen-teams-302478450.html>

### 2.2 Vad rekryterare faktiskt värderar (ISC2 Hiring Trends 2025, 929 rekryterare)

| Siffra | Innebörd |
| --- | --- |
| 90 % | Överväger kandidat med *enbart IT-arbetslivserfarenhet* (ingen utbildning) |
| 89 % | Överväger kandidat med *enbart entry-level-certifiering* |
| 81 % | Överväger kandidat med *enbart utbildning* (IT/säkerhet) — lägst! |
| 3/5 | Tre av de fem toppskattade egenskaperna är **icke-tekniska**: teamwork, problemlösning, analytiskt tänkande |
| — | Topp-5 tekniska: datasäkerhet/kryptering, molnsäkerhet, dataanalys, **AI-färdigheter**, riskbedömning |

Källa: ISC2 2025 Cybersecurity Hiring Trends Report
<https://www.prnewswire.com/news-releases/isc2-research-reveals-organizations-must-amend-early-career-hiring-practices-to-strengthen-teams-302478450.html>
samt sammanfattning med siffror:
<https://professionalsecurity.co.uk/news/commercial-security/cyber-hiring-trends/>

Tolkning från ISC2:s CISO Jon France: *"Hire for attitude, train for aptitude"* — rekrytera på
inställning, lär upp resten. Källa: <https://www.bankinfosecurity.com/isc2-report-entry-level-hiring-needs-reset-a-28741>

**Vår bedömning:** för en karriärbytare betyder det att *dokumenterad praktik* (projekt, lab, cert,
blogg) väger tyngre än examen. Du har fördelen av en YH-examen (praktisk inriktning, LIA-praktik)
plus ett projekt — en stark kombination.

### 2.3 Entry-level-uppgifterna arbetsgivare förväntar sig (ISC2 2025)

Topp-5 uppgifter som arbetsgivare räknar med att entry-level-personal sköter:

1. **Dokumentation** (processer, rutiner) — 43 %
2. **Larm- och händelsehantering** (alert and event management) — 35 %
3. **Rapportering** (ta fram/leverera rapporter) — 32 %
4. **Fysisk åtkomstkontroll** — 30 %
5. **Användarmedvetenhet/utbildning** — 29 %

Källa: ISC2 2025 (samma PR ovan). Detta är guld för dig: SHALLOT *är* ett system för fysisk
åtkomstkontroll, och Cub:s larm-triage + provenanslogg är larm- och händelsehantering med dokumentation.

### 2.4 NICE/NIST-mappning — ramverket som ger dig ett gemensamt språk

**NICE Framework** (NIST SP 800-181 rev. 1) är den internationellt vedertagna katalogen över
cybersäkerhetsarbete, uppbyggd av *tasks* (uppgifter), *knowledge* (kunskap) och *skills* (färdigheter).
Jobbannonser och arbetsgivare använder det för att beskriva roller. Du kan använda samma språk i CV och
portfolio för att "prata deras språk".
<https://csrc.nist.gov/pubs/sp/800/181/r1/final>

**Entry-level-rollen SOC-analytiker = NICE-rollen "Cyber Defense Analyst"** (kategori Protect and
Defend, rollkod 511). Kärnuppgifter: upptäcka/identifiera/varna för intrång, övervaka med försvarsverktyg,
korrelera händelser, dokumentera och eskalera incidenter, trendanalys och rapportering.
Kunskapskrav inkluderar: nätverk och protokoll, intrusionsdetektering (t.ex. IDS/IPS), kryptering,
säkerhetspolicy och sårbarhetsverktyg. Detta är "facit" för vad en SOC-analytiker ska kunna — jämför
med avsnitt 3.
<https://www.cisa.gov/careers/work-rolescyber-defense-analyst>

**Viktig poäng från NIST själva:** NIST förespråkar *kompetensbaserad anställning* ("competency-based
hiring") — anställning baserad på vad du kan visa att du gör, inte på examen. NIST:s vägledning till
arbetsgivare säger till och med: *"Consider removing academic degrees as a non-negotiable requirement"*,
och betonar "show vs. tell". Det stärker strategin att ha ett visningsbart projekt.
<https://nvlpubs.nist.gov/nistpubs/ir/2023/NIST.IR.8355.pdf>
<https://www.nist.gov/system/files/documents/2023/09/22/MTM%20Guidance%20on%20Writing%20a%20Hiring%20Rubric.pdf>

**SANS New-to-Cyber** (välkänd utbildare) ger samma råd direkt till karriärbytare: arbetsgivare
uppskattar kandidater som har **GitHub-bidrag, skrivit blogginlägg eller hållit föredrag på meetups**,
och som byggt en egen hemlab. Vanliga entry-level-titlar: Security Analyst, SOC Analyst,
Junior Security Engineer med flera.
<https://www.sans.org/mlp/new-to-cyber>
<https://assets.contentstack.io/v3/assets/blt36c2e63521272fdc/blt4bdf4bdc6698936a/N2C_Field_Manual.pdf>

### 2.5 AI-säkerhet — den nya dörröppnaren

- AI är den mest efterfrågade säkerhetskompetensen (ISC2 2025, se §2.1), och AI-nämns som krav i
  ~10 % av US-annonserna (CyberSeek 2025, se §2.1). Flera marknadsanalyser ser att AI/ML-krav i
  säkerhetsannonser växer snabbt (t.ex. 8 % → 19 % på en månad enligt en analys av jobbannonser):
  <https://dexity.com/intel/security-ai-career-path-2026> *(analys, ej officiell statistik)*
- **Men grunden kvarstår:** 62 % av säkerhetsproffsen anser inte att AI minskat behovet av
  grundläggande säkerhetskunskaper (ISC2 2026). AI flyttar arbetet *uppåt* mot granskning,
  validering och mänskligt omdöme — just teamwork/analytiskt tänkande.
  <https://www.prnewswire.com/news-releases/isc2-research-finds-ai-is-reshaping-cybersecurity-roles-and-increasing-human-oversight-302822455.html>
- **Hetaste nischen = "security for AI"** (skydda AI-system: prompt-injection, modell-egress,
  agent-auktorisering) — inte "AI for security". Prompt-injection-försvar nämns i annonser som en av
  de vanligaste AI-säkerhetskraven.
  <https://theaimarketpulse.com/ai-for-cybersecurity/skills/>
  <https://owasp.org/www-project-top-10-for-large-language-model-applications/> *(OWASP LLM Top 10)*

**Vår bedömning:** de flesta sökande kan visa "jag använder AI i mitt säkerhetsarbete". *Nästan ingen
kan visa "jag byggde ett system som skyddar mot AI-attacker"*. Cub gör precis det andra — det är din
särskiljare. De flesta AI-säkerhetsroller kräver dock flera års erfarenhet; för entry-level gäller det
att visa *medvetenhet och ett fungerande proof-of-concept*, inte att söka AI-säkerhetstjänst direkt.

### 2.6 Den svenska marknaden

- **Arbetsförmedlingens yrkesprognos (2025):** IT-säkerhetsspecialister hör till yrkena med
  **"mycket liten konkurrens om jobben"** — arbetsgivare har svårt att rekrytera. (Citat via YH-skola
  som citerar prognosen: <https://medieinstitutet.se/utbildningar/it-sakerhetsanalytiker/>;
  officiell sökyta: <https://arbetsformedlingen.se/platsbanken/annonser?q=Cybers%C3%A4kerhet>)
- **SOC-analytiker är den vanligaste ingången för nyexaminerade YH-studenter** i Sverige, och YH är
  den snabbaste vägen till sådana operativa roller (LIA-praktik ingår).
  <https://itjobb.se/sv/guide/it-sakerhet-utbildningsvagar-och-specialiseringar>
- **Konkret annons (Truesec, SOC-analytiker):** krav = grundläggande kunskaper i nätverk, Linux/bash
  och grundläggande kodförståelse; SIEM/EDR/NDR meriterande men *inte krav* — "vi lär dig verktygen".
  Det bekräftar ISC2:s bild: inställning + grund > verktygsvana.
  <https://se.linkedin.com/posts/linus-jorenbo-60013589_cybersecurity-analyst-soc-truesec-activity-7130181255039451139-LPxw>
- **Konkret annons (E-hälsomyndigheten, Cybersäkerhetsanalytiker):** krav = utveckling i Python/Bash/
  PowerShell, IT-nätverk/serverinfrastruktur; meriterande = SOC/SIEM-arbete (Splunk), certifieringar
  (OSCP, CEH, CySA+ m.fl.). Observera: "relevant akademisk utbildning *alternativt likvärdig
  arbetslivserfarenhet*" — erfarenhet väger mot examen även i offentlig sektor.
  <https://e-halsomyndigheten.varbi.com/se/what:job/jobID:922906/type:job/where:125/apply:1>
- **AI/LLM-säkerhet är svagt representerad i svensk högre utbildning** (studie av svenska
  masterprogram): AI-säkerhet, ML-säkerhet och molnsäkerhet är bara marginellt i obligatoriska
  kurser. Det betyder att *den som kan visa det själv har ett försprång på den svenska marknaden*.
  <https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1769241/full>

---

## 3. Vad projektet redan visar (audit mot §2)

Läst i repot: `README.md`, `CONTEXT.md`, `docs/adr/0001–0006`, `docs/DEVELOPMENT-LOG.md`,
`docs/research/` (5 noter), `docs/specs/` (4 specar), `demo/` (auth-server + 9 tester) och
`cub/` (prototyper: scrubber, router, gateway, egress, hitl, memory, tools, simulate_ux).

### 3.1 Mappning mot "vad arbetsgivare söker"

| Vad arbetsgivare söker (källa) | Vad projektet visar | Var |
| --- | --- | --- |
| Hands-on erfarenhet > betyg (ISC2 §2.2) | Fungerande auth-server mot **riktig FIDO2-hårdvara** (ESP32 + pico-fido2, USB HID), 9 tester, attestation-verifiering | `demo/`, `docs/DEVELOPMENT-LOG.md` |
| Fysisk åtkomstkontroll — entry-level-uppgift (ISC2 §2.3) | Hela projektet är **OT-åtkomstkontroll** (SHALLOT-bricka + presence-heartbeat) | `CONTEXT.md`, `README.md` |
| Dokumentation — toppuppgift (ISC2 §2.3) | 6 ADR:er, utvecklingslogg, 5 forskningsnoter, 4 specar (inkl. pentest-scenarier och användbarhetsutvärdering) | `docs/` |
| Larm-/händelsehantering (ISC2 §2.3) | Cub: larm-triage, logg-normalisering, GRC/SIEM-verktyg, egress-monitor som larmar | `cub/tools/grc_siem.py`, `cub/egress/__init__.py` |
| Autentisering/IAM — topp-5 teknisk kompetens | WebAuthn/FIDO2/CTAP 2.2, attestation, roller (mama_bear/cub), minsta privilegium | `demo/`, ADR 0003 |
| AI-färdigheter i annonser (CyberSeek/ISC2 §2.5) | LLM-agent med **prompt-injection-försvar**, egress-verifiering, AI Act/GDPR/NIS2-mappning | `cub/egress/`, ADR 0006 |
| Riskbedömning/GRC (ISC2 §2.1) | Ramverk genomgående: NIST CSF 2.0, SP 800-53r5, MITRE ATT&CK, CIS v8, AI Act-art. 12/14 | `CONTEXT.md`, ADR 0006 |
| Analytiskt tänkande, problemlösning (ISC2 §2.2) | Forskning → design → beslut: MITRE T1078-not, CTAP2-feasibility, alert-fatigue-not | `docs/research/` |
| Kommunikation/icke-teknisk förmåga | Användbar säkerhet (usable security): heuristik-spec + LLM-simulerad användare | `docs/specs/`, `cub/simulate_ux.py` |

### 3.2 Det här är projektets starkaste argument (vår bedömning)

1. **Främsta särskiljare: säkerhet *för* AI.** Cub är uttryckligen designad för noll
   kontrollplanet-rättigheter, med ingress-scrubbing, policy-routing (modellen väljer aldrig sin tier),
   egress-verifiering (deny + injektionstest) och HITL-grind med provenanslogg (ADR 0006). Det är
   "security for AI"-berättelsen som de flesta YH-studenter inte kan visa — och som matchar den hetaste
   kompetensbristen (ISC2 §2.5).
2. **Äkta hårdvara, inte mock.** Riktig ESP32-bricka registrerad mot servern över USB HID, plus
   faktiskt inköpt PicoFIDO-material och budgetredovisning. Det svarar på "show, don't tell" (NIST §2.4).
3. **Dokumenterad beslutslogg.** Varje val är en ADR med motiv och konsekvenser. ISC2:s toppuppgift
   "dokumentation" är bokstavligen levererad.
4. **Icke-tekniska bevis:** användbarhets-arbetet (spec + simulering) och threat-modell-tänket
   (MITRE-mappning) visar analytiskt tänkande och kommunikationsförmåga — de egenskaper ISC2 rankar
   högst (§2.2).

### 3.3 Vad som *inte* visas idag (ärlig audit)

- **SOC-analytiker-kärnan saknas:** paket- och nätverkstrafikanalys, riktig SIEM (Splunk/Elastic/Wazuh),
  IDS/IPS, forensik. `grc_siem.py` nämner OSS-stacken men prototypen skriver till en lokal fil.
  Vill du söka SOC-analytiker rakt av räcker inte detta projekt ensamt — se lucka 4.
- **Inget offentligt narrativ.** README:en är skriven *för utvecklare*, inte för en rekryterare eller
  HR. Det finns ingen karta "projekt → jobbkrav", ingen demo, inga skärmbilder/video, inga blogginlägg.
- **Repot är internt** (privat repo på GitHub). SANS-rådet "GitHub-bidrag och blogginlägg" (§2.4)
  kräver att någon kan *se* arbetet.
- **Certifiering saknas** — den enda pusselbiten som öppnar ATS-såll (automatiska CV-filter) och matchar
  "89 % överväger entry-level-cert" (§2.2).
- **Delar av Cub är stubs** (scrubber = TODO, memory = TODO, abstraction = tom katalog på en branch).
  Det är OK för en prototyp, men i en portfolio ska "färdigt och testat" vara det som syns — stubs ska
  inte döljas men inte heller vara framsidan.

---

## 4. Konkreta luckor och rekommenderade åtgärder (rankat: effekt ÷ insats)

> Prioritet beräknad som *sannolik effekt på anställningsbarheten* ÷ *tidsinsats*. 1 = gör först.

### 1. Bygg det offentliga narrativet (hög effekt, låg insats)
- Skapa en **portfolio-första sida** (antingen gör repot offentligt eller gör en publik portföljkopia):
  vad SHALLOT+Cub är, vilka säkerhetsproblem de löser, 3–5 skärmbilder och en 3–5 min **demovideo**
  (registrera passkey → logga in → visa Cub:s egress-verifiering blockera en prompt-injection).
- Skriv en karta **"projekt → jobbkrav"** med ord från riktiga annonser: *FIDO2/WebAuthn, IAM, NIST-ramverk,
  larm/triage, dokumentation, Python, Linux, prompt-injection*. Lägg den högst upp i README och på LinkedIn.
- Skriv **1–2 blogginlägg** (svenska): "Phishing-resistent OT-åtkomst med WebAuthn" och
  "Varför min LLM-agent har noll kontrollprivilegier" (egress + HITL + AI Act). SANS listar blogg som
  ett bevis arbetsgivare uppskattar (§2.4). Bloggen *är* beviset på icke-tekniska egenskaper (§2.2).
- Källa för att detta är rätt grepp: SANS New2Cyber Field Manual (§2.4) och NIST "show vs tell" (§2.4).

### 2. Koppla till SOC-analytiker-rollen med en mini-SOC-artefakt (hög effekt, medel insats)
- Bygg en liten, färdig **logganalys + triage + rapport**-demon på demo-serverns egna loggar:
  normalisera loggar, detektera ett brute-force/T1078-mönster (ni har redan MITRE-noten!), triage med
  ramverksmärkning, generera en incidentrapport via provenansloggen. Det gör att `grc_siem.py` blir en
  *berättelse* som matchar entry-level-uppgifterna larmhantering (35 %) och rapportering (32 %) (§2.3).
- Det kräver ingen ny teknik — bara att koppla ihop befintliga prototyper och spela in/dokumentera resultatet.

### 3. "Säkerhet för AI"-writeup + färdig demo (hög effekt, medel insats)
- Skriv upp vad Cub bevisar mot **OWASP LLM Top 10 / prompt-injection** och AI Act art. 12/14
  (ni har mappningen i ADR 0006). Visa injektionskorpus-testet (`cub/egress/__init__.py`) som körande
  demo med skärmdump av PASS/FAIL.
- Positionera det *som det är*: ett labb-bevis, inte produktionssystem (ADR 0006 gör detta ärligt — behåll det).
- Varför: AI är den vanligaste kompetensbristen (ISC2 §2.1) och annonskravet växer (§2.5).

### 4. Fyll en verklig kompetenslucka: nätverk + SIEM + intrångsdetektering (medel effekt, medel insats)
- Om målet är SOC-analytiker rakt av: lägg till ett litet självstudie-labb (t.ex. Wazuh/ELK i VM, en
  tcpdump/Wireshark-övning, en Snort-regel) och dokumentera det i samma portfolio. Jämför med NICE:s
  Cyber Defense Analyst-krav (intrusion detection, network traffic analysis — §2.4) och Truesec-annonsen
  (nätverk, Linux/bash — §2.6). Detta stänger det ärliga gapet i §3.3.

### 5. Slutför användbarhetsutvärderingen med riktiga personer (medel effekt, medel insats)
- Ticket #18/`docs/specs/usable-security-evaluation.md`: genomför testet med mänskliga deltagare.
  Ett användartest med rapport visar teamwork, kommunikation och analytiskt tänkande — ISC2:s topp-3
  (§2.2) — och fysisk åtkomstkontroll/användarmedvetenhet (ISC2 §2.3). Simuleringen (`simulate_ux.py`)
  är ett bra förstadium, men *människor* är det starka beviset.

### 6. Entry-level-certifiering (medel effekt, låg/medel insats)
- Satsa på en instegscert (t.ex. CompTIA Security+ eller CySA+): 89 % av rekryterarna överväger
  entry-level-cert (§2.2), certet är meriterande i svenska annonser (E-hälsomyndigheten nämner CySA+
  §2.6) och det passerar ATS-såll som inte läser ditt projekt. Projektet hjälper dig plugga — ramverken
  är redan inne i huvudet.

### 7. Lyft fram svenska arbetsmarknadsargumentet (låg effekt att glömma, gratis)
- På LinkedIn/CV: citera inte prognosen rakt av, men använd dess konsekvens — "arbetsgivare har svårt att
  rekrytera; jag har en YH-examen med LIA plus ett dokumenterat säkerhetsprojekt" (§2.6). Det gör dig
  till en *lättrekryterad* kandidat i en bristsituation.

---

## Källförteckning (primära källor)

- NIST NICE Framework, SP 800-181 rev. 1: <https://csrc.nist.gov/pubs/sp/800/181/r1/final>
- NIST IR 8355 (kompetensbaserad anställning): <https://nvlpubs.nist.gov/nistpubs/ir/2023/NIST.IR.8355.pdf>
- NIST MTM-hyresrubrik ("show vs tell", ta bort examen som krav): <https://www.nist.gov/system/files/documents/2023/09/22/MTM%20Guidance%20on%20Writing%20a%20Hiring%20Rubric.pdf>
- Cyber Defense Analyst (NICE 511): <https://www.cisa.gov/careers/work-rolescyber-defense-analyst>
- CyberSeek (arbetsmarknadsdata): <https://www.cyberseek.org/> och
  <https://www.comptia.org/en/about-us/news/press-releases/CyberSeek-expands-cybersecurity-workforce-data-coverage-and-enhances-user-experience/>
- ISC2 2025 Hiring Trends Report: <https://www.prnewswire.com/news-releases/isc2-research-reveals-organizations-must-amend-early-career-hiring-practices-to-strengthen-teams-302478450.html>
- ISC2 2025 Workforce Study via EU Digital Skills: <https://digital-skills-jobs.europa.eu/en/latest/opinions/skills-based-hiring-europes-best-defence-meeting-cybersecurity-skill-needs>
- ISC2 2026 AI-rapport: <https://www.prnewswire.com/news-releases/isc2-research-finds-ai-is-reshaping-cybersecurity-roles-and-increasing-human-oversight-302822455.html>
- ISC2 "Entry-Level Hiring Needs a Reset": <https://www.bankinfosecurity.com/isc2-report-entry-level-hiring-needs-reset-a-28741>
- SANS New2Cyber Field Manual: <https://assets.contentstack.io/v3/assets/blt36c2e63521272fdc/blt4bdf4bdc6698936a/N2C_Field_Manual.pdf> och <https://www.sans.org/mlp/new-to-cyber>
- Svensk marknad: Medieinstitutet (AF-prognos 2025): <https://medieinstitutet.se/utbildningar/it-sakerhetsanalytiker/> ·
  itjobb.se (SOC som ingång): <https://itjobb.se/sv/guide/it-sakerhet-utbildningsvagar-och-specialiseringar> ·
  Truesec SOC-annons: <https://se.linkedin.com/posts/linus-jorenbo-60013589_cybersecurity-analyst-soc-truesec-activity-7130181255039451139-LPxw> ·
  E-hälsomyndigheten: <https://e-halsomyndigheten.varbi.com/se/what:job/jobID:922906/type:job/where:125/apply:1> ·
  AI-säkerhet i svensk utbildning (Frontiers): <https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1769241/full>
- AI-säkerhetstrender (analyser, ej officiella): Dexity <https://dexity.com/intel/security-ai-career-path-2026> ·
  AI Pulse <https://theaimarketpulse.com/ai-for-cybersecurity/skills/> ·
  OWASP LLM Top 10: <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
