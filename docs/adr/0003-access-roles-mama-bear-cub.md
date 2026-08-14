# Åtkomstroller: Mama Bear / Cub

Tre begrepp skiljs åt i SHALLOT:
- **SHALLOT / Smart ID-bricka** — FIDO2-hårdvaran (PicoFIDO/ESP32), själva autenticatorn.
- **Cub** — agenten (mjukvara) som *hostas* antingen på Arduino UNO Q eller på Fedora (Linux). Cub agerar mot ID-brickan för åtkomst.
- **Mama bear** — admin/gateway-åtkomstpunkt (separat PicoFIDO).

I `demo/`-servern modelleras `mama_bear` och `cub` som WebAuthn-users; credentialt som lagras är SHALLOT-ID-brickan (FIDO2-nyckeln). Valet är en gränsbeslut (scope) som är svårt att byta sedan UI och datamodell byggts kring det.

**Consequences:** Vilken stack Cub-agenten kör — Arduino UNO Q (C/C++) vs Fedora (Python) — är **inte spikad** (se wayfinder-ticket om Cub-agent-stack). Proximity-verifieringen (heartbeat/Transit) är ännu inte kopplad till auktorisationsbeslutet (#4 / #15).
