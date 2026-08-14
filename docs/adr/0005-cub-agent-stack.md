# Cub-agent: Pydantic AI + lokal Ollama, sandboxed

Cub-agenten är en LLM-baserad AI-agent (modell-agnostisk) som inom SHALLOT-ekosystemet
hanterar GRC, SIEM-auditering, loggkontroll och larmhantering. Stacken beslutad via
`design-an-interface` (3 parallella designs) + `grill-with-docs` — fördjupning av ADR 0004
(Cub hostas på Fedora/Python).

**Considered Options:** LangGraph (explicit state-graf), rå function-calling (ingen
framework), LangChain (fullt ekosystem), Pydantic AI + explicit tool-allowlist.

**Decision:** Pydantic AI (lean, typ-säker, liten attack-yta) + en egen explicit
tool-allowlist/flödeskontroll. Standard-modell = **lokal Ollama** (ingen egress, inga
API-nycklar, air-gap-vänligt); moln (OpenAI/Anthropic) är opt-in via secret-store.
Agenten sandboxes i **rootless Podman** (drop caps, read-only rootfs, seccomp, nätverk
låst till enbart provider).

**Consequences:**
- Säkerhet är A och O: minsta beroendeyta, ingen extern egress som default, blast radius
  begränsad av allowlist — inte av modellens fria vilja.
- FIDO/CTAP, SIEM/logg, GRC och larm exponeras som smala tools (allowlist per kontext);
  modellen väljer endast inom tillåten lista → begränsar skada vid prompt-injection.
- Prompt-injection-mitigation: olitlig data (loggar/larm) isoleras från instruktioner;
  tool-inputs är strukturerade (aldrig fri text styr verktygsval).
- Modell-agnostisk via Pydantic AI providers (Ollama lokalt + moln opt-in) — byter modell
  utan kodändring.
- Kostnad: mindre "färdig" graf än LangGraph; flödeskontroll egenkodad men liten och
  granskningsbar. Bygger vidare på ADR 0004 (Fedora/Python) och återanvänder `demo/`-logik.
