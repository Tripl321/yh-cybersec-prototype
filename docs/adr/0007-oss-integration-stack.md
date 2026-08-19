# SHALLOT: OSS-integrationsstack

Fördjupning av ADR 0005/0006. Denna ADR specificerar *vilka* OSS-plattformar som
integreras i SHALLOT och *varje komponents roll*. Besluten togs via `grill-with-docs`
-grillning av alla komponenter i cub-agenten och demo-servern.

## Beslutade komponenter

| Komponent | OSS-plattform | License | Roll |
|-----------|---------------|---------|------|
| WebAuthn RP | Hanko | AGPL-3.0 | FIDO2/passkey-server, user management |
| Observability | Latitude | MIT | LLM-sporing, MCP-server |
| Persistent minne | Supermemory | MIT | Episodiskt/semantiskt minne, RAG |
| SIEM | Wazuh | Free, open source | Loggning, larm, MITRE-mappning, compliance |
| Ingress Scrubber | AES-SIV (`cryptography`) | Apache-2.0 | Deterministisk kryptering av entiteter |
| Egress-sandbox | Podman | Apache-2.0 | Rootless container, deny-by-default |
| HITL | Pydantic AI deferred tools | MIT | Konsekvensbaserat beslut + provenans-logg |
| FIDO CTAP | Hanko (backend) | AGPL-3.0 | Wrappar Hankos API för hårdvarudriver |
| Transit | LoRa SX1262 | HW | Heartbeat-protokoll över radio |
| Agent-framework | Pydantic AI | MIT | Redan beslutat (ADR 0005) |
| Modell | Ollama (llama3.2) | MIT | Redan beslutat (ADR 0005/0006) |

## Motivering per komponent

### Hanko (WebAuthn RP)

**Varför inte behålla egen Flask-RP?** Hanko är en etablerad, FIDO2-certifierad
plattform med 9k stars. EU-baserad (Tyskland). AGPL-3.0 för backend, MIT för frontend.
Ersätter `demo/app.py` + `demo/db.py` med en beprövad lösning. Stöder Keycloak-plugin
för SSO. Webhooks för audit-loggar.

**thesis-signal:** Visar att du kan välja och integrera en beprövad plattform, inte
bara bygga från grunden. Starkare för "praktisk OT-säkerhet".

### Latitude (Observability)

**Varför inte Logfire?** Latitude erbjuder bättre LLM-sporing: varje anrop, varje
tool-användning, varje failure spåras. MCP-server ger direkt integration. Self-hosted.
Ersätter Logfire i `cub/__main__.py`.

### Supermemory (Persistent minne)

**Varför inte Milvus eller Mem0?** Supermemory vinner på prestanda (95% Recall@15)
och enkelhet (en binär, noll config). MIT-licensat. Kör offline via Ollama.
Täcker episodiskt + semantiskt + procedurt minne + RAG. Ersätter `cub/memory/__init__.py`.

### Wazuh (SIEM)

**Varför inte JSONL-fil?** Wazuh är en riktig SIEM med MITRE ATT&CK-mappning
(redan i cub-agents framework_tags), compliance-rapportering (NIST CSF, CIS Controls),
och agent-baserad övervakning. API för integration med cub-agenten. Dashboard i
OpenSearch/Kibana. Mer realistiskt för thesis.

### AES-SIV (Scrubber)

**Varför inte FPE?** NIST drog tillbaka FF3/FF3-1 i februari 2025 pga sårbarheter.
AES-SIV via `cryptography` (redan beroende) ger deterministisk kryptering utan
underkänd standard. Reversibel via lokal nyckel.

### Podman (Egress-sandbox)

**Varför inte enklare lösning?** Redan beslutat i ADR 0005. Rootless container med
drop caps, read-only rootfs, seccomp, nätverk låst till provider. Visar att du
förstår container-säkerhet.

### Pydantic AI deferred tools (HITL)

**Varför inte egen lösning?** Kombination: Pydantic AI:s deferred tools ger
HITL-mekanismen (AI Act art. 14), egen provenans-logg + rubber-stamp-mätning
ger thesis-unik spårning.

### Hanko (FIDO CTAP backend)

**Varför inte python-fido2?** Din `fido_ctap.py` har redan en placeholder för
USB HID. Hanko hanterar redan FIDO2. CTAP-tool blir en tunn wrapper mot Hankos API.

### LoRa SX1262 (Transit)

**Varför inte serial/USB?** Hårdvaran redan inköpt (2× Core1262-HF). LoRa ger
OT-realistisk radiokommunikation. Starkare thesis-signal.

## EU-efterlevnad (uppdatering)

| Pelare | Lag/ramverk | OSS-komponent |
|---|---|---|
| Lokal-först (ingen egress) | GDPR art. 25; NIS2 21(2)(a) | Podman deny-by-default |
| Ingress-scrub + AES-SIV | GDPR 5(1)(c) minimering | `cryptography` AES-SIV |
| Model Router (policy) | AI Act 9, 12, 15 | Pydantic AI + router |
| Human-in-the-loop | AI Act 14 | Pydantic AI deferred tools |
| Provenans-logg | AI Egen provenans-logg |
| SIEM | NIST CSF, MITRE ATT&CK | Wazuh |
| FIDO2/WebAuthn | NIST SP 800-63B | Hanko |
| Data-minimering | GDPR 5(1)(c) | Supermemory TTL/purge |

## Consequences

- Alla komponenter är open source (AGPL, MIT, eller Apache-2.0).
- Lokal-först: inga API-nycklar, inga molntjänster som default.
- Modell-agnostisk: Ollama lokalt, moln opt-in (ADR 0006).
- SIEM-integration med Wazuh ger MITRE-mappning och compliance utan extra kostnad.
- Hanko ger FIDO2-certifiering och production-ready auth.
- Supermemory ger persistent minne utan egen vektor-DB-infrastruktur.
- Kostnad: mer arkitektur (fler komponenter) men låg löpande kostnad (alla OSS).
