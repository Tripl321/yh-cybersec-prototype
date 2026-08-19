# Problemformuleringens tre påståenden — verifiering mot primärkällor

*Skrivet för: examensarbetets författare (inte för säkerhetsexperter).*
*Metod: endast primärkällor (myndighetsdokument, standarder, granskade vetenskapliga publikationer, branschundersökningar). Bloggsammanfattningar är uteslutna. Alla källor är US/EU-baserade; svenska sektorspecifika rapporter har inte hittats under detta sökpass och nämns inte.*

---

## 1. Slutsats i korthet

| Påstående | Bedömning |
|---|---|
| Claim 1: OT-åtkomstkontroll använder fortfarande ofta gamla, oreviderbara mekanismer (fysiska nycklar, delade inloggningsuppgifter, pappersloggar) | **SUPPORTED** |
| Claim 2: Nätfiske/lösenordsattacker är ett reellt hot även mot OT, som kräver nätfiskesäker autentisering (FIDO2/WebAuthn/passkeys); användningen av FIDO2 i OT är fortfarande låg | **SUPPORTED** (delstöd för "låg användning" — se not) |
| Claim 3: Det finns ett användarvänlighetsglapp i OT-åtkomstkontroll — mänskliga faktorn är en känd svag punkt, och lösningarna måste fungera för operatörer som inte är säkerhetsexperter | **SUPPORTED** |

---

## 2. Claim 1 — OT-åtkomstkontroll bygger ofta på gamla, oreviderbara mekanismer

**Bedömning: SUPPORTED.**

### Bevis

- **NIST SP 800-82r3**, *Guide to Operational Technology (OT) Security* (sept 2023), är USA:s officiella vägledning för OT-säkerhet. Den skriver rakt ut att delade inloggningsuppgifter är vanliga i OT: *"Shared credentials are often used on OT systems"*, och att lösenordsanvändning har kända svagheter (standardlösenord, lösenord som delas och inte byts, lösenord som skickas okrypterat). Dokumentet konstaterar också att delade lösenord gör det omöjligt att avgöra *vem* som faktiskt gjorde vad — dvs. de är inte reviderbara i efterhand. När OT-utrustning inte stödjer autentisering rekommenderar NIST fysiska skydd som kompensation, t.ex. *"control center keycard access"* — en fysisk nyckel/kortlösning som norm, inte undantag.
- **Nosouhi et al., *Towards Availability of Strong Authentication in Remote and Disruption-Prone OT Environments*** (ACM, 2024, granskad konferenspublikation). Studien beskriver hur nätverksadministratörer i praktiken "deploy weak authentication methods for remote OT systems and assets and share credentials with a group of users" för att personalen snabbt ska komma in även när systemet är frånkopplat från centrala servrar. Delade lösenord är alltså en etablerad driftlösning, inte en olyckshändelse.
- **CISA *FY22 Risk and Vulnerability Assessment Analysis*** (2023). Analys av 121 säkerhetsbedömningar mot kritisk infrastruktur visar att "default administrator accounts" och icke-återkallade konton var en av de vanligaste svaga punkterna — typiskt för OT-miljöer där standardlösenord aldrig ändras.

**Jargonförklaring:** "OT" = system som styr fysiska processer (el, vatten, fabriker). "Delade inloggningsuppgifter" = flera personer loggar in på samma användarnamn/lösenord. "Reviderbara" = det går att i efterhand se *vem* som gjorde vad i loggar.

### Källa

- NIST SP 800-82r3: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf (översiktssida: https://csrc.nist.gov/pubs/sp/800/82/r3/final)
- Nosouhi et al. 2024: https://dl.acm.org/doi/fullHtml/10.1145/3664476.3671411
- CISA FY22 RVA: https://www.cisa.gov/sites/default/files/2023-07/FY22-RVA-Analysis%20-%20Final_508c.pdf

---

## 3. Claim 2 — Nätfiske/lösenordsattacker hotar OT, och nätfiskesäker autentisering (FIDO2) behövs men används lite

**Bedömning: SUPPORTED**, med en reservation: själva påståendet om *låg FIDO2-användning i OT* har inget direkt, stort statistiskt underlag — det stöds indirekt av standarder och forskning (se nedan).

### Bevis (nätfiske/lösenord är ett verkligt hot)

- **CISA FY22 RVA Analysis** (2023) är det starkaste beviset. I 121 genomförda säkerhetsbedömningar av kritisk infrastruktur (inkl. OT) lyckades angripare nå nätverken genom **valida konton i 54 %** av fallen och genom **spearphishing-länkar i 33 %** av fallen — tillsammans ~87 %, dvs. nästan 9 av 10 lyckade intrång. CISA:s egna rekommendationer pekar ut *"Phishing-Resistant MFA"* (nätfiskesäker flerfaktorautentisering) som motåtgärd (CPG 2.H).
- **CISA/NSA-cybersäkerhetsmeddelande AA22-265A** (2022) slår fast att OT/ICS-säkerhet "inte adekvat hanterar nuvarande hot" och att angripare ofta når kontrollsystem via IT-nätet och fjärråtkomst. Detta förklarar hur nätfiske mot IT-personal blir ett OT-hot.
- **SANS ICS/OT Cybersecurity Survey** (2023): "komprometterade IT-system som ger intrång i OT/ICS-nätverk rankades högst" bland incidentorsaker. En branschundersökning som bekräftar vägen nätfiske → IT → OT.

### Bevis (varför nätfiskesäker autentisering behövs — FIDO2/WebAuthn/passkeys)

- **NIST SP 800-63B-4**, *Digital Identity Guidelines* (2024), är standarden som definierar säkerhetsnivåerna AAL2/AAL3. Den säger att WebAuthn/FIDO2 ger "phishing resistance through verifier name binding": nyckeln är kryptografiskt bunden till den äkta webbplatsen, så ett falskt nätfiskefönster inte kan fånga och återanvända den. Synkade passkeys uppfyller AAL2, enhetsbundna AAL3. Detta är definitionen på varför passkeys är nätfiskesäkra medan SMS-koder och lösenord inte är det.
- **CISA**, *Implementing Phishing-Resistant MFA* (faktablad, 2023) — myndighetens rekommendation att införa nätfiskesäker MFA, främst FIDO/WebAuthn-nycklar, särskilt för fjärråtkomst och privilegierade konton.
- **NIST SP 800-82r3** konstaterar att MFA är "accepted best practice" för fjärråtkomst till OT, men också att "some OT components support only a single factor or no authentication" — dvs. den moderna, nätfiskesäkra autentiseringen finns inte inbyggd i stora delar av OT-ekosystemet.

### Bevis (låg FIDO2-användning i OT — indirekt)

- NIST SP 800-82r3 beskriver OT-läget som enkel-faktor eller ingen autentisering alls, med delade lösenord som norm (se Claim 1).
- Nosouhi et al. (2024) visar att den operativa verkligheten i fjärrstyrd OT är lösenordsdelning, och att MFA är svårt att införa när OT-platser kan kopplas bort från central IAM-infrastruktur.
- Ingen granskad källa hittades som visar bred FIDO2-drift i OT — tvärtom beskriver källorna OT som efter IT när det gäller modern autentisering. **Reservation:** detta är inferens, inte en mätning. Om "låg användning" ska stå i problemformuleringen som ett faktum, bör det omformuleras till "modern, nätfiskesäker autentisering är inte normen i OT enligt standarder och forskning".

**Jargonförklaring:** "Nätfiske" (phishing) = lurendrejerimail som får användaren att lämna ut lösenord. "FIDO2/WebAuthn/passkeys" = teknik där en krypteringsnyckel ligger i enheten (telefon/hårdvarunyckel) istället för ett lösenord; den fungerar bara mot den äkta sajten, så den kan inte "phishas".

### Källa

- CISA FY22 RVA: https://www.cisa.gov/sites/default/files/2023-07/FY22-RVA-Analysis%20-%20Final_508c.pdf
- CISA/NSA AA22-265A: https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-265a
- SANS ICS/OT Survey 2023: https://www.sans.org/white-papers/ics-ot-cybersecurity-survey-2023s-challenges-tomorrows-defenses
- NIST SP 800-63B-4: https://pages.nist.gov/800-63-4/sp800-63b.html
- CISA Phishing-Resistant MFA-faktablad: https://www.cisa.gov/sites/default/files/publications/fact-sheet-implementing-phishing-resistant-mfa-508c.pdf
- NIST SP 800-82r3: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf
- Nosouhi et al. 2024: https://dl.acm.org/doi/fullHtml/10.1145/3664476.3671411

---

## 4. Claim 3 — Mänskliga faktorn är en svag punkt i OT, och lösningarna måste fungera för icke-säkerhetsexperter

**Bedömning: SUPPORTED.**

### Bevis (mänskliga faktorn är en känd svag punkt)

- **Verizon DBIR 2024** (Data Breach Investigations Report, branschstandardens mest citerade undersökning): 68 % av dataintrången involverade "a non-malicious human element" — misstag eller att människor lurade att klicka. Lösenordsstöld (credential misuse) var den vanligaste vägen in. DBIR är inte OT-specifik, men visar att mänskliga faktorn är den enskilt största kategorin — ett allmänt, mätbart faktum som OT-branschen själv hänvisar till.
- **SANS**, *Managing Human Risk in Industrial Control System Environments* (2023): pekar på att "human element" varit inblandad i ~80 % av intrången (enligt DBIR-data) och argumenterar att ICS-operatörer och ingenjörer nu måste tränas i säkerhet — human risk hanteras aktivt, inte bara tekniskt.
- **NIST SP 800-82r3** erkänner operatörens vardag: "A unique challenge in OT is the need for immediate access to an HMI in emergency situations" och rekommenderar att autentiseringskrav vägs mot "the capabilities of the OT and its personnel". Standardens kapitel om medvetenhet och utbildning (PR.AT) förutsätter att OT-personal inte är säkerhetsexperter utan behöver stöd.

### Bevis (användarvänlighetsglapp i OT-åtkomstkontroll — ett öppet forskningsområde)

- **Li, Rashid & Roudaut, *Usable Security Model for Industrial Control Systems — Authentication and Authorisation Workflow*** (EuroUSEC 2023, granskad vetenskaplig konferens). Detta är en direkt, vetenskaplig behandling av problemet: hur autentisering och auktorisering *bör* se ut i ICS för att vara användbar. Att det 2023 fortfarande publiceras konferensartiklar om "vilket arbetsflöde är användbart för autentisering i ICS?" visar att området är omoget — glappet finns.
- **Li, *Usability Study of Security Features in Programmable Logic Controllers*** (2024, konferens). En användbarhetsstudie av säkerhetsfunktionerna i PLC:er (de datorer som styr industrimaskiner) — ytterligare granskad forskning som mäter hur svårt säkerhet är att använda i OT-hårdvara.
- **Nosouhi et al. (2024)** beskriver varför säkerhet skruvas ner i OT: personal måste komma in snabbt även vid driftstörningar, därför delas lösenord. Det är en användbarhetskompromiss — säkerhet offras för att operatörer ska kunna jobba.

**Jargonförklaring:** "Användbarhet" (usable security) = att säkerheten ska vara enkel och snabb att använda i vardagen, annars kringgår människor den. "HMI" = operatörens kontrollskärm för processen.

### Källa

- Verizon DBIR 2024: https://www.verizon.com/business/resources/reports/dbir/ (figurerna även sammanfattade av t.ex. ASIS/SANS, men siffrorna är DBIR:s)
- SANS Managing Human Risk: https://www.sans.org/blog/sans-ics-security-awareness-new-series-managing-human-risk-in-industrial-control-system-environments
- NIST SP 800-82r3: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf
- Li, Rashid & Roudaut, EuroUSEC 2023: https://dl.acm.org/doi/fullHtml/10.1145/3617072.3617114
- Li, PLC-usable study 2024: https://www.researchgate.net/publication/374751906_Usable_Security_Model_for_Industrial_Control_Systems_-_Authentication_and_Authorisation_Workflow
- Nosouhi et al. 2024: https://dl.acm.org/doi/fullHtml/10.1145/3664476.3671411

---

## 5. Vad det betyder för projektets problemformulering

- **Claim 1:** Behåll påståendet, men skriv det som att *standarder och forskning dokumenterar* delade lösenord och fysiska skydd som norm i OT (NIST 800-82r3) — inte som en egen mätning i projektet.
- **Claim 2:** Styrkan ligger i CISA:s siffror (54 % valida konton + 33 % spearphishing). Omformulera "FIDO2-användningen i OT är låg" till det som faktiskt går att belägga: *modern nätfiskesäker autentisering är inte normen i OT enligt NIST och granskad forskning*.
- **Claim 3:** Behåll, men backa upp "mänskliga faktorn" med DBIR (68 %) och användbarhetsglappet med EuroUSEC-studien — på så sätt blir påståendet citerbart i stället för en åsikt.
