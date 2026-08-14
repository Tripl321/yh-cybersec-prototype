# Cub-agent-stack: Fedora (Python)

Cub-agenten hostas som en Python-process på Fedora (Linux). Valet gjordes i ticket #28 (grilling).

Rollmodellen (ADR 0003): SHALLOT = ID-bricka (FIDO2-hårdvara), Cub = agent, Mama bear = admin/gateway. Cub-agenten agerar mot SHALLOT för åtkomst och ska (framtida) köra heartbeat/Transit.

**Considered Options:** Arduino UNO Q (C/C++) som embedded agent, eller Fedora (Python).
**Consequences:** Python valdes för prototypen — det matchar `demo/`-serverns språk (Flask/`webauthn`/`fido2`) och går att testa direkt utan monterad hårdvara. UNO Q är mycket begränsad och kräver monterad hårdvara (#17), så embedded C/C++ lämnas som eventuellt senare härdningssteg. Cub-agenten byggs i Python och kan återanvända `demo/`-logik; heartbeat/Transit (#4 / #15) implementeras i Python-agenten.
