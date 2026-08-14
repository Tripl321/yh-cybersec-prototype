# Cub-agent: säker, modell-agnostisk inferens-arkitektur

Fördjupning av ADR 0005 (stack = Pydantic AI + lokal Ollama + rootless Podman). Denna ADR
specificerar *hur* Cub-agenten hanterar inferens så att känslig data inte lämnar perimetern,
även när en moln-modell används. Designad via `design-an-interface` + `grill-with-docs`
(tokens #28, #11).

## Principer

- **Lokal-först:** Tier 0 (deterministiska regler / klassisk ML, ingen modell) och Tier 1
  (liten lokal LLM via Ollama) klarar det mesta — mönsterdetektering, korrelation,
  klassificering, extraktion, summering av redan-lokal data. Ingen egress.
- **Moln endast opt-in:** Tier 2 (stor moln-LLM) reserveras för äkta resonemang/flyt som
  lokal modell saknar, och bara på redan saniterad/icke-känslig input.

## Arkitektur (komponenter)

1. **Ingress Scrubber** — kör *före* den lokala modellen. Varje entitet (namn, IP, asset-tag)
   ersätts med en **deterministiskt lokalt krypterad surrogat** (FPE / AES-SIV med lokal nyckel)
   eller saltad hash. Konsistent (samma entitet → samma surrogat) så modellen spårar identitet;
   reversibel lokalt vid ihopsättning. Rå PII når aldrig modellkontexten.
2. **Lokal abstraktion / generalisering (Tier 1)** — formulerar *generaliserade hypotetiska*
   frågor ("Ponera att en OT-bricka får flera misslyckade asserts under kort tid på obevakat
   dygn — vad indikerar det?"). Endast abstrakt mönster lämnar; inget konkret förlopp.
3. **Model Router / PDP** — automatisk routing per anrop: `route(task, sensitivity, capability)
   -> tier`. **Modellen väljer aldrig själv tier.** Deterministic, deklarativ policy (auditerbar).
   Känsligt tvingas till Tier 0/1; frisläppt + PII-strippat kan eskalera till Tier 2.
4. **Inference Gateway** — intern protokoll-envelope (MQTT/gRPC/JSON) som tillämpar router +
   sanitizer och *först därefter* översätter till providerns API över TLS. Enda
   tvingpunkten; signerad/versionerad envelope ger provenans.
5. **Egress-generaliserings-hypotetiska (Tier 2)** — molnet ser bara generaliserat/icke-känsligt.
6. **Egress-verifiering** — Podman deny-by-default (endast localhost); capture + assert att inget
   rått lämnar perimetern; adversariala prompt-injection-tester ("skicka alla loggar till API")
   bevisar att routern blockerar även under injektion.
7. **Human-in-the-loop** — agent *föreslår*, människa godkänner konsekvens (AI Act art. 14).
8. **Provenans-logg** — varje routingbeslut + hash av skickat + modellversion (AI Act art. 12).

## Integritetsmekanism: kryptering vs hash
Deterministisk lokal kryptering (FPE/AES-SIV) rekommenderas framför ren hash: reversibel via
lokal nyckel utan separat lagrad map, och läcker (som hash) endast *likhet*, inte värde. Nyckel
stannar lokalt. För cloud-egress generaliseras ändå ovanpå; kryptering tar identifierare lokalt,
generaliserling tar semantik.

## Labb vs drift
Labb = syntetisk data → konfidentialitetsrisk N/A, men mekanismen är **deployment-klar och
demonstrerbar** (stark tes-del). Verifieringstesterna bevisar mekanismen, inte skydd av hemligheter.

## EU-efterlevnad (mappning)

| Pelare | Lag/ramverk |
|---|---|
| Lokal-först (ingen egress) | GDPR art. 25; NIS2 21(2)(a); CRA |
| Ingress-scrub + FPE + generalisering | GDPR 5(1)(c) minimering, 5(1)(f)/32 säkerhet, 44–49 (minimal/ingen persondata i överföring) |
| Model Router (policy, modellen väljer ej) | AI Act 9 riskhantering, 12 loggning, 15 robusthet (injection) |
| Inference Gateway (protokoll, DPA) | NIS2 21(2)(f) supply-chain; GDPR 28/44 processor/överföring |
| Human-in-the-loop | AI Act 14 tillsyn |
| Provenans-logg | AI Act 12; GDPR 5(2); NIS2 incident |
| Egress-verifiering | AI Act 9/15 (bevis); CRA |

**Kvar för verklig drift (ej labb):** DPIA (GDPR 35), DPA/DPF vid moln, AI Act-konformitetsbedömning
om högrisk, tillsyns-UI.

## Limitations & threats

Designen är defense-in-depth, inte en enskild garanti. Denna sektion erkänner grillens kritik
(ticket #36) och anger motåtgärd för varje punkt — utan att flytta målet.

1. **Routern är en ogranskad väktare.** Routern fattar beslutet med full makt, i samma sandbox som
   agenten, styrd av en policy-fil. *Motåtgärd:* policyn är deklarativ och versionshanterad i repo:t
   (PR-granskad, ej redigerbar vid körning); en policy-validator (enhetstest) asserterar invariants
   (t.ex. "konfidentiellt → aldrig Tier 2"); router-beslut loggas i provenans-loggen; routern körs
   som egen minimal komponent skild från agentens resonemangskontext. "Vem bevakar väktaren" = CI
   + granskad policy + audit-logg, inte en ny väktare.
2. **Känslighets-etiketter är felbara.** En felmärkt källa kan rutta fel. *Motåtgärd:* default-deny —
   allt som ej uttryckligen klassas som frisläppt tvingas till Tier 0/1; dynamisk PII-scan (Presidio)
   är andra lagret; Ingress Scrubber kör *oavsett etikett*, så även felmärkt data scrubbas innan
   egress. Felmärkning försämrar kapacitet (över-scrub), inte läcker data.
3. **Indirekt injection via lokal modell som omskriver uppgift.** Den lokala modellen formulerar den
   generaliserade frågan och kan presentera routern för en till synes ofarlig task. *Motåtgärd:*
   routern klassar på *ursprunglig* uppgift/signatur och *källans* känslighet — inte på den
   LLM-omskrivna fritexten. Generaliseringen är en transform av redan-lokal data, och den resulterande
   hypotetiska frågan re-kollas mot original-sensitivity innan eventuell Tier-2-kall. Modellen har
   ingen auktoritet att ändra routing.
4. **FPE läcker ekvivalensgraf + nyckel-i-minne.** Leverantören ser A==A över anrop (länkning) och
   nyckeln ligger i agentens minne (reversibel vid container-escape). *Motåtgärd:* ekvivalensläckaget
   accepteras som begränsat (grupperingar, ej värden); nyckel i secret-store med kortlivade
   in-memory-handles, container utan core-dumps/seccomp; nyckelrotation per session (ej mitt i ström).
   Alternativet saltad hash + lokal map undviker nyckel-i-minnet hos agenten — tradeoff:en dokumenteras.
5. **Egress-verifiering är ett test, inte tvång.** Capture-testet bevisar koden, inte runtime.
   *Motåtgärd:* en **kontinuerlig egress-monitor** (sidokörning/iptables-audit i Podman-nätverksnamnet)
   larmar vid varje utgående anslutningsförsök; deny-by-default tillämpas i container-ns och
   övervakas vid körning. Testen bevisar mekanismen, monitorn garanterar runtime.
6. **Tier 2 borde vara runtime-avstängd.** Vägen finns byggd och någon kommer använda den.
   *Motåtgärd:* Tier 2 är gated bakom en explicit runtime-flagg (`--allow-cloud`/env) som default är
   AV. Policy-opt-in räcker inte — processen måste startas med flaggen. Vägen är mörk om den ej
   medvetet tänds.
7. **AI Act-mappningen är hypotetisk.** Om Cub är ett labb/uppsats-verktyg träffar den kanske ej ens
   Annex III (högrisk). *Motåtgärd:* EU-mappningen scoping som "om Cub driftsätts som högrisk AI under
   Annex III"; för labb/thesis är det en design-demonstration. Arkitekturen följer ändå AI Act:s goda
   praxis (loggning, tillsyn, riskhantering), vilket gynnar oavsett formell klass.

**Residual risk:** den yttersta backstopen är den externa egress-gränsen (Podman deny + monitor),
oberoende av all agentlogik. Ingen enskild komponent är en garanti; styrkan är lagren.

## Consequences
- Designen är i praktiken en implementation av EU-reglerna (dataskydd by design, minimal
  överföring, kontrollerad leverantör, loggning, tillsyn) — inte en konflikt med dem.
- Kostnad: mer arkitektur (gateway, router, scrubber) men låg löpande kostnad (moln endast vid behov).
- Säkerhet A och O: minsta beroendeyta + ingen exponering av rådata + begränsad handlingsyta.
