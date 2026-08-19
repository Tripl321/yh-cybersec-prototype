# Research Note: Alert fatigue — detektering och undvikande (SOC/SIEM & HITL under EU:s AI-förordning)

**Frågeställning:** Bästa praxis för att upptäcka och undvika "alert fatigue" (larmtrötthet) i (1) SOC/SIEM-alarmhantering och (2) mänsklig tillsyn (HITL) av AI-system enligt artikel 14 i EU:s AI-förordning — med tillämpning på SHALLOT/Cub:s godkännandeflöde för att förhindra "rubber-stamping" (klickgodkännande).

**Författare:** AI Agent  
**Datum:** 2026-08-15  
**Status:** Completed

---

## Primärkällor

1. **NIST SP 800-61r3** — *Computer Security Incident Handling Guide* (april 2025). [NIST.SP.800-61r3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf)
2. **ENISA** — *How to set up CSIRT and SOC* (december 2020). [ENISA-rapport](https://www.enisa.europa.eu/sites/default/files/publications/ENISA%20Report%20-%20How%20to%20setup%20CSIRT%20and%20SOC.pdf)
3. **EU AI Act** — Regulation (EU) 2024/1689, artikel 14 och skäl (72)–(73). [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689)
4. **NIST AI RMF 1.0** — *Artificial Intelligence Risk Management Framework* (NIST AI 100-1, 2023). [doi.org/10.6028/NIST.AI.100-1](https://doi.org/10.6028/NIST.AI.100-1)
5. **Drew, B. J. et al. (2014)** — *Insights into the problem of alarm fatigue with physiologic monitor devices: A comprehensive observational study of consecutive intensive care unit patients*. PLoS ONE 9(10):e110274. [journals.plos.org](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0110274)
6. **The Joint Commission** — *Sentinel Event Alert, Issue 50: Medical device alarm safety in hospitals* (8 april 2013). [PDF-mirror (KFF)](https://www.kff.org/wp-content/uploads/sites/8/2013/04/sea_50_alarms_4_5_13_final1.pdf)
7. **Goddard, K., Roudsari, A., Wyatt, J. C. (2012)** — *Automation bias: a systematic review of frequency, effect mediators, and mitigators*. JAMIA 19(1):121–127. [doi.org/10.1136/amiajnl-2011-000089](https://doi.org/10.1136/amiajnl-2011-000089)
8. **Tariq, S., Baruwal Chhetri, M., Nepal, S., Paris, C. (2025)** — *Alert Fatigue in Security Operations Centres: Research Challenges and Opportunities*. ACM Computing Surveys 57(9). [doi.org/10.1145/3723158](https://doi.org/10.1145/3723158)
9. **Baruwal Chhetri, M. et al. (2024)** — *Towards Human-AI Teaming to Mitigate Alert Fatigue in Security Operations Centres*. ACM TOIT 24(3). [doi.org/10.1145/3670009](https://doi.org/10.1145/3670009)
10. **Skonieczny, K. m.fl. (2025)** — *AI-Driven Security Alert Screening and Alert Fatigue Mitigation in SOCs: A Comprehensive Survey*. arXiv:2605.08316. [arXiv](https://arxiv.org/html/2605.08316v1)

---

## Sammanfattning

Alert fatigue uppstår när volymen larm/förfrågningar överväldigar människan så att varningssignaler inte längre får någon kognitiv respons — och den mänskliga kontrollen blir meningslös. Detta är ett väldokumenterat problem i både sjukvårdsmiljö (80 dödsfall av 98 anmälda alarmrelaterade händelser på fyra år; upp till 99 % av larmen kräver ingen intervention) och SOC-miljö (överväldigande alarmvolymer, utbrändhet, förlängd breach dwell-time). EU:s AI-förordning artikel 14 kräver explicit att system designas så att mänsklig tillsyn är **faktiskt** möjlig och effektiv — inklusive att operatören ska vara medveten om och motverka *automation bias* (överreliance på systemets utdata).

Detektering bygger på att mäta (a) alarmvolymer och falsk-positiv-frekvens, (b) beteendesignaler som avfärdande/override-takt, ackumuleringstid och snabba godkännandekluster, samt (c) kvalitetskvoter som konverteringsgrad larm → incident. Undvikande handlar om att sänka brusnivån vid källan (tuning, dedup, korrelation, prioritering) och att höja beslutsfrik­tionen där kostnaden av ett fel är hög (konsekvensbaserade prompts, krav på motivering, spot-check-granskning, rotation), dvs. exakt motsatsen till "auto-approve allt".

---

## 1. Vad är alert fatigue?

**Definition.** I vårdkontext definierar The Joint Commission alarm fatigue som att kliniker "blir avtrubbade eller immuna mot ljuden och överväldigas av information" till följd av ständigt brus; som svar sänker de volymen, stänger av larm eller justerar inställningar utanför säkra gränser. [Källa 6]

I SOC-kontext definieras alert fatigue som att "den enorma mängden larm överväldigar SOC-analytiker och ökar risken att kritiska hot missas" [Källa 9], med vetenskapligt belagda konsekvenser i form av analytikerutbrändhet och förlängd breach dwell-time (tiden en attackerare är obemärkt inne i nätverket). [Källa 10]

**Konsekvenser i vården (kvantifierat).**
- 98 alarmrelaterade händelser rapporterade till The Joint Commission jan 2009–juni 2012: 80 resulterade i dödsfall, 13 i permanent funktionsförlust, 5 i oförutsedd extra vård. Händelserna är kraftigt underrapporterade; 94 av 98 skedde på sjukhus, främst telemetri, IVA, akutmottagning. [Källa 6]
- FDA:s MAUDE-databas: 566 alarmrelaterade patientdödsfall jan 2005–juni 2010, bedömd kraftigt underrapporterad. [Källa 6]
- En observationsstudie på en medicinsk/kirurgisk IVA (Drew et al. 2014): **2 558 760 larm på 31 dagar** på 461 bäddar; **187 hörbara larm per bädd och dygn**; **88,8 % av de annoterade arytmilarmen var falska positiva**; 93 % av de sanna VT-alarmen varade inte tillräckligt länge för att kräva behandling. Studien visar en direkt koppling mellan alarm fatigue och en patientdöd (en lågpulsalarm som vårdpersonal inte uppfattade). [Källa 5]
- "Det uppskattas att mellan 85 och 99 procent av alla larmsignaler inte kräver klinisk intervention" — default-inställningar ändras inte, sensorer hamnar fel etc. [Källa 6]

**Konsekvenser i SOC (kvantifierat).**
- Den akademiska forskningen pekar på stora dagliga alarmvolymer, bred falsk-positiv-börda och växande utredningsköer i SOC:er som huvudproblem. [Källa 10] Lösningar diskuteras utmed tre spår: automation, augmentation och human–AI-kollaboration. [Källa 8]
- NIST sammanfattar kärnan: larm som inte är tillräckligt trimmade skapar så mycket brus att det äter analytikertid — därav kravet att ständigt "trimma kontinuerlig övervakningsteknik för att minska falska positiva och falska negativa till acceptabla nivåer" (DE.CM, s. 24). [Källa 1]

---

## 2. Detektering — hur vet man att alert fatigue pågår?

### 2.1 Volym- och kvalitetsmått (SOC/SIEM)

ENISA anger att en SOC bör mäta och följa upp specifika KPI:er, inklusive: **detektionshastighet, detektionsbredd, täckning, falsk-positiv-frekvens, förhållandet larm/händelser/incidenter, eskaleringar och arbetsbelastning per incident** (s. 8). [Källa 2]

NIST SP 800-61r3 kräver aktiv "tuning" av övervakningsverktyg som en grundläggande funktion (DE.CM), och att analysfunktioner ska **filtrera stora händelsedataset ner till en delmängd lämplig för mänsklig analys** samt beakta kända falska positiva vid incidentklassificering (DE.AE). [Källa 1]

Konkreta mätbara signaler på alert fatigue:

| Signal | Vad man mäter | Koppling |
|---|---|---|
| Alarmvolym | Larm per analytiker och skift; larm per enhet och dygn | När volymen överstiger människans processkapacitet uppstår fatigue [Källa 5, 6] |
| Falsk-positiv-frekvens | Andel larm som vid granskning visar sig vara falska | 85–99 % i vårdmiljö visades göra larm meningslösa [Källa 6]; NIST kräver aktivt FP-reducering [Källa 1] |
| Avfärdande/override-takt | Andel larm som stängs av eller godkänns utan granskning | Direkt beteendemått på desensibilisering — människor "stänger av" bruset [Källa 6] |
| Ackumuleringstid (time-to-ack) | Distribution av tiden från larm till kvittering/åtgärd | Växande fördröjningar indikerar köbildning och avtrubbning [Källa 2] |
| Konverteringsgrad | Kvot larm → händelse → incident | ENISAs KPI "ratio alerts/events/incidents" — om konverteringsgraden kollapsar har man endast brus [Källa 2] |
| Godkännandekluster | Snabba, seriella godkännanden med konstant intervall | Mönster av "klickande utan granskning" (rubber-stamping) — se automation bias [Källa 7] |
| Arbetsbelastning/kö | Utredningskö, backlog, övertid | ENISA listar arbetsbelastning per incident som KPI [Källa 2]; köerna växer i SOC:er [Källa 10] |

### 2.2 Beteendesignaler i HITL-godkännanden (SHALLOT/Cub)

För ett AI-styrt agentflöde där en mänsklig operatör godkänner högriskin­satser (t.ex. "Cub") bör följande mätas kontinuerligt som tidiga varningssignaler på rubber-stamping:

- **Godkännandegrad ≈ 100 %** över tid — om operatören aldrig avvisar eller ifrågasätter saknas reell tillsyn.
- **Beslutstidsdistribution** — en orealistiskt snäv och snabb distribution (t.ex. allt godkänt < 2 s) är ett starkt tecken på att prompten bara klickas igenom, utan att operatören tillgodogjort sig informationen.
- **Överride-/avvikelsegrad** — hur ofta operatören överrider systemets rekommendation. Noll överriders över längre tid är varningssignal, inte en kvalitetsgaranti (jfr automation bias nedan).
- **Överensstämmelse med konsekvens** — om samma åtgärd godkänns snabbt vid lågrisk och långsamt/avvisas vid högrisk är tillsynen fungerande.

Belägg för varför dessa signaler fungerar: Goddard et al. visar att automation bias (se 4.2) yttrar sig som *omissionsfel* (att missa att göra det systemet inte föreslår) och *kommissionsfel* (att blint följa systemets felaktiga förslag); en systematisk granskning fann att beslutstödssystem **ökade sannolikheten för ett inkorrekt beslut med 26 %** (RR 1,26; 95 % CI 1,11–1,44). [Källa 7] Beteendesignalerna ovan fångar just dessa felslag.

---

## 3. Undvikande — best practices

### 3.1 Sänk bruset vid källan (SOC/SIEM)

1. **Kontinuerlig tuning (NIST R2).** NIST 800-61r3, s. 24: *"R2: Tune the continuous monitoring technologies to reduce false positives and false negatives to acceptable levels."* — övervakningsverktyg ska stämmas av löpande; detta är en förutsättning för att mänsklig granskning ska vara meningsfull. [Källa 1]
2. **Fil­trera och korrelera innan människan ser något (NIST DE.AE).** Använd tekniska lösningar för att reducera stora händelsemängder till en granskningsbar delmängd, och väg in kända falska positiva när incident ska förklaras (DE.AE-08). [Källa 1]
3. **Riskbaserad prioritering, inte köordning (NIST RS.MA).** Incidenttriage ska prioriteras och eskaleras utifrån riskfaktorer och affärskritikalitet — "first come, first served" uttryckligen avråds. Detta är det enskilt viktigaste skyddet mot att brus kväver kritiska larm. [Källa 1]
4. **Prioritering/”learning to defer”.** Akademin föreslår alert prioritisation och "learning-to-defer"-modeller där systemet aktivt delegerar osäkra ärenden till människan i stället för att överösa med allt. [Källa 8, 9]
5. **Följ upp ENISA-KPI:erna löpande** (2.1) som en styrprocess — volym, FP-frekvens och konverteringsgrad ska vara ledningsmått, inte slumpartade observationer. [Källa 2]

### 3.2 Designa bort rubber-stamping i HITL-flöden (SHALLOT/Cub)

Direkt tillämpbart på Cub:s godkännandeflöde för högriskåtgärder (t.ex. reboot av produktion, ändring av accesspolicy, exfiltration av data till verktyg):

1. **Konsekvensbaserad prompt, inte "Godkänn?"-standard.** Visa *vad* som görs, *varför* agenten vill göra det, *vilka resurser/känslighet* som påverkas och *konsekvenser* — operatören ska kunna fatta ett informerat beslut. Goddard et al. finner att DSS-design (position, framträdande plats, konfidensnivåer, "information"-kontra "kommando"-formulering) modererar automation bias. [Källa 7]
2. **Forcing functions för högriskbeslut.** Kräv att operatören anger motivering (fritext eller val) för godkännande av kritiska åtgärder, och tillämpa tvåpersonsprincipen för de allra känsligaste åtgärderna — detta speglar AI-förordningens artikel 14(5) (kräver separat verifiering av två fysiska personer för biometrisk identifiering), och är ett beprövat mönster mot klickfelsgodkännanden. [Källa 3]
3. **Rotera ansvar och gör stickprovsgranskning (audit).** Tillsynspersonens beslut ska loggas och en andel stickprovsgranskas av annan person. Goddard et al. visar att *ansvarsskyldighet* (accountability) minskar automation bias, och att *träning* i systemets begränsningar hjälper. [Källa 7]
4. **Sänk antalet onödiga godkännanden (reducera bruset).** Samma princip som SIEM-tuning: automatisera säkra, lågriskåtgärder och batcha/digestisera informationsnotiser så att operatören bara får beslut som verkligen kräver mänskligt omdöme. Alert fatigue uppstår just när människan överväldigas av volym. [Källa 5, 6, 10]
5. **Stopp-knapp (kill-switch).** Operatören ska kunna avbryta/stoppa pågående åtgärd. Detta är ett explicit lagkrav i artikel 14(4)(e) (”stop”-knapp), men också en central åtgärd för att skapa reell, inte bara nominell, kontroll. [Källa 3]
6. **Visa osäkerhet/konfidens.** När agenten rapporterar hur säker den är på ett utfall minskar risken för blind överreliance; konfidensvisning är en av de DSS-designfaktorer som modererar automation bias. [Källa 7]

### 3.3 Mänskliga faktorn som skyddsåtgärd

- **Träning** i systemets kapaciteter/limiteringar och i konsekvenserna av att missa larm (omissionsfel) är en belagd mitigator. [Källa 7]
- NIST AI RMF betonar att mänsklig bedömning och tillsyn ska vara inbyggd, övervakad och mätbar — governance-aktiviteter ska säkerställa att människor kan ingripa, övervaka och avstänga/modifiera systemets kapaciteter. [Källa 4]

---

## 4. EU:s AI-förordning artikel 14 — vad lagen faktiskt kräver

### 4.1 Kärnkraven (art. 14)

- **14(1):** Högeffektiva AI-system ska "utformas och utvecklas på ett sådant sätt ... att de **kan övervakas på ett effektivt sätt av fysiska personer under den period de används**". [Källa 3]
- **14(2):** Mänsklig tillsyn ska "förebygga eller minimera riskerna för hälsa, säkerhet eller grundläggande rättigheter", särskilt när riskerna kvarstår trots andra krav.
- **14(3):** Tillsynsåtgärderna ska vara **proportionerliga mot risk, autonomigrad och användningskontext**, och säkerställas genom (a) åtgärder inbyggda av leverantören i systemet, eller (b) åtgärder som leverantören identifierat och som är lämpliga att genomföra av distributören (deployern).
- **14(4):** Systemet ska levereras så att de fysiska personer som tilldelats tillsyn kan, i lämplig omfattning:
  - **(a)** förstå systemets kapaciteter och begränsningar och övervaka driften, inkl. att upptäcka anomalier, dysfunktioner och oväntad prestanda;
  - **(b)** "**vara medvetna om den möjliga tendensen att automatiskt förlita sig på eller överförlita sig på utdata** som genereras av ett högeffektivt AI-system **(automation bias)**, särskilt för system som ger information eller rekommendationer för beslut av fysiska personer";
  - **(c)** korrekt tolka systemets utdata;
  - **(d)** i varje enskild situation besluta att inte använda systemet eller att ignorera, **överrida eller vända utdata**;
  - **(e)** ingripa i driften eller avbryta systemet via en **"stop"-knapp** eller liknande procedur. [Källa 3]
- **14(5):** För vissa system (biometrisk identifiering) krävs att inget beslut fattas på basis av systemets utdata om inte resultatet **separat verifierats och bekräftats av minst två fysiska personer** med nödvändig kompetens, utbildning och befogenhet. [Källa 3]
- **Skäl (73):** Systemet ska vara "responsivt inför den mänskliga operatören", tillsynspersoner ska ha "nödvändig kompetens, utbildning och befogenhet", och systemet ska inkludera "mekanismer som vägleder och informerar" tillsynspersonen om "när och hur man ska ingripa för att undvika negativa konsekvenser eller risker, eller stoppa systemet". [Källa 3]

### 4.2 Varför rubber-stamping är en överträdelse

Artikel 14(1) kräver *effektiv* tillsyn — inte en fysisk person som klickar igenom. Punkt 14(4)(b) nämner automation bias **uttryckligen** som en risk tillsynspersonen måste vara medveten om och motverka. Automation bias är väldokumenterad: systematisk genomgång visar att användare gör både omissionsfel (missar vad systemet inte föreslår) och kommissionsfel (följer felaktiga systemförslag) och att beslutstöd ökar risken för inkorrekta beslut med 26 %. [Källa 7]

Ett flöde där operatören godkänner 100 % av åtgärderna utan variation i beslutstid levererar inte de kognitiva funktioner lagen förutsätter (förståelse, tolkning, överriding). Det är i praktiken varken (a), (b), (c) eller (d) uppfyllt. Det innebär också ett reellt säkerhetshål: med 99 % falska positiva larm "stängs" människan av och de sanna larmen drunknar (jfr vårdexemplet där en patient dog på en icke-uppfattad larmsekvens). [Källa 5, 6]

---

## 5. Tillämpning på SHALLOT/Cub — konkret checklista

För SHALLOT (FIDO2/WebAuthn-baserad OT-accesskontroll) med en lokal LLM-agent ("Cub") som dirigerar åtgärder efter känslighet och kräver operatörsgodkännande för högriskåtgärder:

1. **Instrumentera godkännandeflödet** med mätpunkterna i avsnitt 2.2 (godkännandegrad, beslutstidsdistribution, override-grad) och exponera dem i en dashboard.
2. **Trimma vilka åtgärder som kräver godkännande** — allt som är säkert/reversibelt ska vara automatiserat; bara beslut med verklig konsekvens ska nå operatören (jfr NIST R2/ENISA-volymprinciperna).
3. **Konsekvensbaserade godkännandeprompts** med känslighets- och konsekvensinfo samt konfidens från agenten.
4. **Forcing functions:** kräv motivering för högriskgodkännanden; tvåpersonsverifiering för de allra känsligaste åtgärderna (art. 14(5)-modell).
5. **Stopp-knapp** på alla pågående åtgärder (art. 14(4)(e)).
6. **Loggning + stickprovsgranskning och rotation** av tillsynsrollen (accountability mitigierar automation bias).
7. **Träning** av operatörer i Cub:s kapaciteter/limiteringar och i automation bias (art. 14(4)(b), skäl 73).

---

## 6. Slutsats

Alert fatigue är mätbart, förebyggbart och — i EU-sammanhang — rättsligt relevant. Samma mönster gäller för SOC-analytiker och för operatörer som godkänner AI-åtgärder: när volymen är för hög och friktionen för låg blir den mänskliga kontrollen skenbar snarare än verklig. Detektion sker via volym-, kvalitets- och beteendemått; undvikande sker genom brusreducering vid källan (tuning, korrelation, prioritering) kombinerat med design som höjer beslutsfriktionen där fel kostar (konsekvensbaserade prompts, motiveringskrav, tvåpersonskontroll, audit, stopp-knapp). Artikel 14 i AI-förordningen gör detta till ett lagkrav för alla distributörer av högeffektiva AI-system.
