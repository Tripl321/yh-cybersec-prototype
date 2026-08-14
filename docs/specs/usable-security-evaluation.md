# Utvärdering av usable security — SHALLOT

> Utkast/plan för ticket [#18](https://github.com/Tripl321/yh-cybersec-prototype/issues/18).
> Syfte: mäta i vilken grad SHALLOT är *användbart säker* (usable secure) jämfört med baseline.

## Varför
"Secure by design" räcker inte om operatören inte kan använda systemet säkert i
praktiken. Usable security är ett starkt examens- och employability-perspektiv och
saknas i nuläget i prototypen.

## Forskningsfrågor (RQ)
- **RQ1:** Upplevs SHALLOT som användbart jämfört med baseline (fysisk nyckel + papperslogg)?
- **RQ2:** Klarar operatörer utföra åtkomst (registrera passkey, logga in) utan allvarliga fel?
- **RQ3:** Motstår lösningen nätfiske i praktiken (phishing-resistance)?

## Rekommenderad metod (baserat på etablerad forskning)
1. **SUS (System Usability Scale)** — standardmått, 10 frågor, 0–100. Acceptabelt golv
   ≈ 68 (Ruoti et al., SOUPS 2016; Reese et al., SOUPS 2019). Ges efter varje system
   (SHALLOT och baseline) för direkt jämförelse.
2. **Think-aloud** under uppgifter — fångar kognitiv process (Creswell/standard).
3. **Task success / SEQ** — genomförandegrad, tid, antal fel, Single Ease Question per task.
4. **Jämförelse mot baseline** — samma uppgifter med fysisk nyckel + papperslogg.
5. **(Valfritt) Phishing-scenario** — demonstrera att en stulen credential inte räcker för
   att imitera användaren (FIDO2 är phishing-resistent); mät operatörens riskförståelse.

## Metrik
- **Kvantitativt:** SUS-medelvärde (SHALLOT vs baseline), task completion rate,
  time-on-task, felantal, SEQ.
- **Kvalitativt:** tematisk analys av think-aloud + kort intervju.
- **Säkerhet:** phishing-resistance (ja/nej) + operatörens upplevda riskförståelse.

## Protokoll (förslag)
1. Bakgrundsenkät (demografi, IT-vana).
2. Uppgifter med SHALLOT: registrera passkey (roll `cub`/`mama_bear`), logga in,
   ev. heartbeat. Think-aloud.
3. SUS + kort intervju.
4. Samma uppgifter med baseline (fysisk nyckel + papperslogg).
5. SUS + jämförande intervju.

## Deltagare (förslag)
- N = 5–10 (klasskamrater / personer med OT-relevans). Inom YH ofta begränsat underlag.

## Analys
- Jämför SUS SHALLOT vs baseline (parat test / deskriptivt). Tematisk analys av kvalitativt.
- Bonneau et al. UDS-ramverk (Usability–Deployability–Security) kan användas som
  inspektions-baserad komplettering.

## Hot mot validitet
- Litet N, ej representativa användare. **Roll-spel påverkar säkerhetsbeteende**
  (Schechter et al., "Emperor's New Security Indicators") → använd helst egna konton/risker
  snarare än roll-spel där det går.

## Beslut (grilling — ticket #18, 2026-08-14)
- **Metodmix:** SUS + think-aloud + task success, jämfört mot **baseline** (fysisk nyckel + papperslogg). Phishing-scenario ingår **ej** i piloten.
- **Deltagare:** Pilot **1–2 personer** (think-aloud) — lägsta tröskel för att komma igång.
- **Etik:** Ingen IRB för pilot omfång 1–2, men dokumentera muntligt + skriftligt samtycke
  och anonymisering.
- **Nästa steg:** genomför pilot, samla SUS + think-aloud-transkription + baseline-jämförelse,
  och skriv in resultatet här.
