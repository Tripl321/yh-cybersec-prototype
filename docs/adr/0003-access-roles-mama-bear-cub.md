# Åtkomstroller: Mama Bear / Cub

SHALLOT modellerar två roller — `mama_bear` (admin/gateway-åtkomstpunkt) och `cub` (fältnod / ID-bricka) — som WebAuthn-users med varsin credential-uppsättning i `demo/`-servern.

Rollerna definieras i `CONTEXT.md`; servern behövde en konkret auktoriseringsmodell. Valet är en gränsbeslut (scope) som är svår att byta sedan UI och datamodell byggts kring den.

**Consequences:** Proximity-verifieringen (heartbeat/Transit) är ännu inte kopplad till auktorisationsbeslutet — det är öppet i kartan (#4 / #15). Attestation verifieras inte i demo-läget (`attestation=none`); om PicoFIDO-attestation ska bindas till kända nycklar är det en egen fråga (#14).
