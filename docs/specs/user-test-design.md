# Specification: SHALLOT Användartest-design (User-Test Design)

**Issue:** [#5](https://github.com/Tripl321/yh-cybersec-prototype/issues/5) (T6 Grilling)  
**Author:** AI Agent & Johannes  
**Date:** 2026-08-13  
**Status:** Resolved (grilled)

---

## 1. Overview

Denna spec beskriver utvärderingsmetoden för **Beroende 3 – Användarupplevelse** i SHALLOT (se variabeltabell i kartan #1): SUS-poäng + uppgiftslatens, med kontrollvariabeln *deltagarens tekniska nivå*. Metoden är framförhandlad via grillning (#5) och avgränsad av kursens ramar.

---

## 2. Kurskontext (scope-driver)

- **Kurs:** Cybersäkerhet projektarbete, **20 YH-poäng = 4 veckor heltid**.
- **Examination:** slutrapport (metod + analys + lösning) + presentation + reflektion. Betyg G/IG/VG.
- **VG-kriterium:** *"fördjupad analys, självständighet och kvalitet i genomförande och presentation"* — kräver **inte** extern part eller stor N.
- **Konsekvens:** ingen empirisk, power-beräknad användarstudie ryms på 4 veckor bredvid prototypbygge + rapport. Metoden hålls lättviktig och ärligt avgränsad.

---

## 3. Forskningsdesign (Q1)

**Within-subjects (repeated measures) med counterbalanserad ordning** (ABBA / Latin square).
Varje pilot-deltagare upplever båda villkoren (Baseline och SHALLOT) → kontrollerar individuella skillnader och kräver litet N. Carry-over-effekt hanteras med randomiserad startordning och counterbalansering.

---

## 4. Deltagare & rekrytering (Q2, Q7)

- **Population:** YH cybersecurity-studenter / tekniskt orienterade personer i författarens närhet (convenience sample, fungerar som proxy för OT-operatörer).
- **Metoden byggs inte på grupp.** Urvalsstorlek och rekrytering är oberoende av om arbetet görs enskilt eller i grupp.
- **Optionell extern person:** en extern kontakt (t.ex. från en OT-verksamhet) *kan* involveras i ett **mindre, avgränsat test** som komplement — men detta är frivilligt ("gärna" i kursens Syfte), inte ett VG-krav.
- **Kontrollvariabel:** deltagarens tekniska nivå (självskattad) samlas in och rapporteras som deskriptiv fördelning; används inte för formell statistisk justering vid pilot-omfattning.

---

## 5. Omfattning (Q3)

**Primär metod (alltid):** heuristisk utvärdering enligt [`docs/specs/usable-security-heuristics.md`](docs/specs/usable-security-heuristics.md) (H1–H8) + **expert-SUS** (författare och eventuella peer-reviews).

**Tillägg (OM tid/rekrytering finns):** mini-pilot, **think-aloud, n≈4–5**, SUS + uppgiftslatens. Rapporteras **explorativt/pilot** — ej power-beräknat.

**Fallback:** 2–3 peer-walkthroughs (tänk-högt) utan formell SUS-aggregation.

Allt flaggas ärligt i rapportens Metod-avsnitt som pilot/explorativt, inte som definitiv empirisk studie.

---

## 6. Scenario & uppgift (Q4)

Ett scriptat **"OT-terminalåtkomst"**-scenario, genomfört för båda villkoren:

- **Baseline:** hämta fysisk nyckel → lås upp skåp/dörr → skriv i pappersloggbok → utför definierad åtgärd (t.ex. "starta/logga in på OT-terminal").
- **SHALLOT:** tryck PicoFIDO-knapp (auth) → gå in i närvarozonen (passivt Transit-heartbeat) → utför samma åtgärd → läs E-ink-status (`AUTHENTICATED` / `OUT OF RANGE: LOCKED`).
- **Tidsmätning:** från "påbörja åtkomst" till "åtgärd klar".

---

## 7. Mätinstrument (Q5)

- **Expert-SUS** (0–100) per villkor — baslinje för jämförelse.
- **Vid pilot:** SUS (0–100) per villkor, **uppgiftslatens** (sekunder), **fel/hjälp-räkning**, samt **2–3 öppna debrief-frågor** (t.ex. "Vad kändes osäkert?", "Vilket villkor litar du mest på?").
- **Analys:** renodlat **deskriptiv** jämförelse (median, spridning, effektstorlek vid pilot) + kvalitativa citat. Ingen inferens-statistik vid pilot-N.
- Koppling: resultatet matar Beroende 3 (användarupplevelse) och validerar H1–H8 (särskilt H2 Synlighet, H3 Minimal börda, H5 Felstatus).

---

## 8. Etik & säkerhet (Q6)

- Muntligt informerat samtycke vid pilot (ingen formell etikansökan vid n≈5; bekräfta med handledare).
- Endast självskattad teknisk nivå som persondata — **pseudonymiserat**, inga namn i rådata.
- **Li-Po-säkerhetsgenomgång** för deltagare (ej punktera/kortsluta; hantera varsamt).
- Ingen ansikts-/ljudinspelning utan explicit samtycke.

---

## 9. Tidplan (4 veckor, crude)

| Vecka | Fokus |
|---|---|
| 1 | Prototypbygge (hårdvara #9) + heuristisk utvärdering (H1–H8) + expert-SUS |
| 2 | Pilot-scenario + rekrytering (tech-peers), genomförande, SUS/latens |
| 3 | Analys, rapport (Metod/Analys/Lösning), ev. extern mini-test |
| 4 | Reflektion, presentation, finslipning |

---

## 10. Koppling till övriga issues

- **#4** Heuristik-ramverk (H1–H8) — primär UX-metod här.
- **#3** MITRE T1078-mappning — täcker Beroende 2 (säkerhetspostur), ej detta test.
- **#8** Rapportstruktur — denna spec blir Metod-avsnittet i slutrapporten.
- **#9** Hårdvara — piloten kräver monterad badge + gateway.

---

## Next Steps
- **Issue #5 outcome:** Resolved (grilled). Träd: Q1 within-subjects · Q2 tech-peers · Q3 lättviktig · Q4 OT-scenario · Q5 SUS+latens · Q6 etik · Q7 ej gruppbaserad.
- Specen matar #8 (rapportstruktur) och prototyp-ticket #7.
