# Wayfinder Map — SHALLOT Secure-by-Design ID-bricka

## Destination

En komplett projektbeskrivning för YH (cybersecurity officer-programmet) som demonstrerar en mätbar säkerhetsförbättring genom en "secure by design"-utvecklad smart ID-bricka (SHALLOT) med proximity-baserad åtkomstkontroll och MFA, jämfört med en traditionell baseline-lösning i en OT-labbmiljö. Projektet ska kombinera UX/design-kompetens med cybersäkerhet och förankras i NIST CSF 2.0, MITRE ATT&CK, CIS Controls v8 och NIST SP 800-53.

### Huvudfrågeställning

> *"I vilken utsträckning kan en 'secure by design'-utvecklad smart ID-bricka med proximity-baserad åtkomstkontroll och flerstegsautentisering (SHALLOT) förbättra säkerhetsposturen i en OT-labbmiljö jämfört med en traditionell åtkomstlösning, och hur påverkas användarupplevelsen av denna förbättring?"*

### Delfrågor

1. **Secure by design:** Hur integreras principerna för secure by design (minsta privilegium, defense in depth, fail-safe defaults) i SHALLOT:s arkitektur för smart ID-bricka, och hur mappar detta mot NIST SP 800-53 IA-familjen och NIST CSF PR.AC-kontroller?
2. **Säkerhetspostur:** Hur förändras mitigeringen av MITRE ATT&CK-tekniken T1078 (Valid Accounts) när SHALLOT:s smarta ID-bricka ersätter traditionell nyckelbricka/PIN som baseline?
3. **Ramverksmappning:** Vilka NIST CSF 2.0-kontroller (PR.AC-1, PR.AC-2, PR.AC-7) och CIS Control 6-subkontroller implementeras eller stärks av SHALLOT, och vilken funktionell förbättring representerar detta?
4. **Användarupplevelse:** Hur påverkar SHALLOT:s designelement (E-ink-feedback, krypterat heartbeat-larm, QR-MFA, secure-by-design-defaults) upplevd användbarhet, effektivitet och tillfredsställelse jämfört med baseline, mätt via System Usability Scale (SUS) och uppgiftslatens?

### Variabler

| Typ | Variabel | Mätmetod |
|---|---|---|
| Oberoende | Åtkomstmetod (fysisk nyckel + pappersloggbok vs SHALLOT smart ID-bricka) | Kontrollerad labbuppsättning |
| Beroende 1 | Secure by design-mognad | Kvalitativ analys mot NIST SP 800-53 IA + PR.AC-kontroller |
| Beroende 2 | Säkerhetspostur | MITRE ATT&CK T1078-mappning + NIST CSF Profile-jämförelse |
| Beroende 3 | Användarupplevelse | SUS-poäng + tidsmätning av åtkomstflöde |
| Kontroll | Deltagarens tekniska nivå | Självskattning före test |

---

## Notes

### Pocock-skills-flöde
Projektet följer Matt Pococks skill-flöde:
1. `setup-matt-pocock-skills` — konfigurera repo (issue-tracker, labels, CONTEXT.md) ✅ FULLFÖRD
2. `grill-with-docs` — domänmodell + CONTEXT.md + ADRs (OT/ICS-termer, SHALLOT-arkitektur)
3. `wayfinder` — kartlägg öppna beslut
4. `to-spec` — wayfinder-besluten → formell spec
5. `to-tickets` — spec → implementerbara tickets
6. `prototype` — HTML-prototyp av SHALLOT UI/UX-flöde (flera varianter)
7. `implement` + `tdd` — bygg prototypen med feedback-loopar
8. `code-review` — granska mot spec + standarder

### UX-säkringsmetod (beslutad)
NIST SP 800-63B + usable security-heuristik som designkrav. Heuristisk utvärdering av både baseline och SHALLOT innan användartest. Designprinciper:
- "Make the secure path the easy path" — säker metod får inte kräva fler steg
- "Visible security" — användaren ser att säkerheten är aktiv (E-ink)
- "Minimal user burden" — autentisera en gång, verifiera passivt (heartbeat)

### PicoFIDO-arkitektur (beslutad)
Två PicoFIDO-enheter med strikt separation — en för fältåtkomst, en för admin ("mama bear"). Båda bygger på Raspberry Pi Pico 2 W (RP2350).

---

## Decisions-so-far

1. **Destination**: YH projektbeskrivning (ej demo-pitch, ej enbart byggbar spec)
2. **Riktning**: SHALLOT — kombinerar UX och cybersäkerhet
3. **Frågeställning**: Akademisk formulering med secure by design + smart ID-bricka, 4 delfrågor, variabeltabell
4. **UX-metod**: Heuristik + principer (NIST SP 800-63B + usable security-heuristik som designkrav)
5. **Pocock-flöde**: Fullt flöde från setup till code-review
6. **PicoFIDO-arkitektur**: Två enheter, strikt separation. Pico #1 = fält-ID-bricka (IA-2(2)), Pico #2 = admin/mama bear (IA-2(1)). Båda RP2350.
7. **Baseline**: Fysisk nyckel + pappersloggbok. Analog, 0 SEK, minimal scope. Attacker: nyckelkopiering, loggboks-förfalskning, ingen spårbarhet.

---

## Child Tickets

- [x] Setup Pocock-skills för repo (Task)
- [ ] #2 Research: NIST SP 800-63B usable security-principer
- [ ] #3 Research: MITRE ATT&CK T1078 mitigeringar med PicoFIDO
- [x] Baseline-lösning — ✅ LÖST (Fysisk nyckel + loggbok)
- [ ] #4 Grilling: Usable security-heuristik-val (Blocked by #2)
- [ ] #5 Grilling: Användartest-design (Blocked by #4)
- [ ] #6 Grilling: Pen-test-scenarier (Blocked by #3)
- [ ] #7 Grilling: SHALLOT prototyp-omfattning och hårdvara (Blocked by #5, #6, #9)
- [ ] #8 Grilling: Rapportstruktur för YH (Blocked by #5, #6)
- [ ] #9 Research: SHALLOT hårdvaruarkitektur och kostnad
- [ ] #10 Grilling: PicoFIDO-integration med SHALLOT (Blocked by #3, #8)
