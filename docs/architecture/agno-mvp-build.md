# Agno MVP — Build Reference

> Build-ref för implementationen av SHALLOT-harness på Agno (spårval #74 → ADR 0010 → ticket #82).
> Allt här verifierat mot docs.agno.com (primärkälla) 2026-08-27.

## Arkitekturöversikt (ADR 0010)

MSP (2 dagar): Agno v3 runtime-kärna + befintlig custom PWA (Next.js/shadcn, `shallot-setup`).
Lokalt Ollama (RTX 4080 16GB), local-first via Tailscale, secret/confidential stannar lokalt.

| Komponent (befintlig) | → Agno-primitiv/kapabilitet |
|---|---|
| `agent.py` (Agent + 7 tools + systemprompt) | `Agent(model=…, tools=[…], instructions=…)` |
| `server.py` (hembyggd SSE) | `AgentOS(...).get_app()` / `serve("...:app")` |
| `policy.py` (policy/HITL) | HITL-approval (känsliga tools), guardrails/hooks |
| `store.py` SQLite / `memory.py` | `SqliteDb` → `PostgresDb` + pgvector (post-MVP) |
| context (git/github/repo) | egna verktyg / Context Providers (GitHub-mcp) |
| `ledger.py` (GitHub canonical) | behålls som tool |
| reasoner-stub | `Workflow` (två-modellers-kedja) post-MVP |

## Install & setup

```bash
uv pip install -U "agno[os]" ollama   # AgentOS-extra; ollama-extra namnkontrolleras vid install
```

- Dev: `python agentos.py` → AgentOS-server på **`localhost:7777`**.
- `AgentOS` importeras `from agno.os import AgentOS`; FastAPI-app via `.get_app()`.

```python
from agno.agent import Agent
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb

shallot = Agent(
    name="SHALLOT",
    model="ollama:ministral-3:8b-instruct-2512-q4_K_M",  # alternativ: Ollama(id="ministral-3:8b-…")
    instructions=SYSTEM_PROMPT,
    tools=[...7 tools...],
    db=SqliteDb(db_file="tmp/agents.db"),
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)
agent_os = AgentOS(agents=[shallot])
app = agent_os.get_app()
if __name__ == "__main__":
    agent_os.serve("agentos:app", reload=True)
```

## Modell & verktyg

- Modell: lokal `ministral-3:8b` via Ollama. String-shorthand `"provider:model"` (t.ex. `"openai:gpt-5.5"`) eller klass-import från `agno.models.ollama`.
- De 7 befintliga tools portas lector (`@tool`): `get_project_state`, `get_event_history`, `run_harness`, `search_memory`, `add_memory`, `approve_action`, `get_budget_status`.
- Känsliga verktyg (t.ex. `approve_action`, Harness/exekvering, budget) → **approval-required** (HITL).
## Memory & storage

- MVP: `SqliteDb(db_file=...)` + `enable_agentic_memory` + `add_history_to_context`/`num_history_runs`.
- Post-MVP: `PostgresDb` + **pgvector** (RAG), durable sessions.
- **Alternativ (post-MVP) — Memori** (docs.agno.com, /memory/memori): persistent, sökbart conversation-minne,
  LLM-agnostiskt, DB-agnostiskt (PostgreSQL/MySQL/SQLite/MongoDB/Cockroach/Neon/Supabase/Oracle).
  Smart attribution per `entity_id` (→ SHALLOT-node) och `process_id` (→ processtyp) — passar vår domänmodell.

```python
uv pip install -U agno memori openai sqlalchemy python-dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from memori import Memori

engine = create_engine("sqlite:///memori_agno.db")   # ell. PostgreSQL via DATABASE_PATH
Session = sessionmaker(bind=engine)
mem = Memori(conn=Session).llm.register(model.get_client())
mem.attribution(entity_id="node/paw-01", process_id="OT-op")
mem.config.storage.build()
```

> Källa: https://docs.agno.com/memory/memori · https://github.com/MemoriLabs/Memori · https://memorilabs.ai/docs/

## Observability (post-MVP)

- Agno avger **OpenTelemetry-traces** (industristandard): auto-instrumentering av agents+tools, flexibel export
  till valfri OTel-kompatibel backend; custom-tracing.
- OTB-backends: AgentOps, Arize Phoenix, Langfuse, LangSmith, Langtrace, LangWatch, Logfire, Maxim, MLflow,
  OpenLIT, Traceloop, Weave, m.fl.
- **SHALLOT**: egen DB som backend (post-MVP; lokal-first — ingen extern telemetri-tjänst krävs).

> Källa: https://docs.agno.com/features/observability.md

### MLflow (rekommenderad lokal-first, OSS + self-host, en rad)

```bash
pip install -U mlflow agno openai yfinance        # kräver mlflow>=3.3
mlflow server                                     # lokal spår-servrar på localhost:5000
export MLFLOW_TRACKING_URI="http://localhost:5000"
```

```python
import mlflow
mlflow.agno.autolog()        # en rad — spårar model/tool/anrop automatiskt
agent_os = AgentOS(agents=[shallot], tracing=True)  # AgentOS: streaming/auth/session + spår
```

### OTel → hosted backend (opt-in, post-MVP · drift #80: endast public + opt-in)

Kanoniskt exempel: LangSmith via OpenInference+OTel.

```bash
uv pip install -U agno openai openinference-instrumentation-agno opentelemetry-sdk opentelemetry-exporter-otlp
export LANGSMITH_API_KEY=... LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com LANGSMITH_PROJECT=...
```

```python
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

endpoint = f"{request['LANGSMITH_ENDPOINT'].rstrip('/')}/otel/v1/traces"
headers = {"x-api-key": request['LANGSMITH_API_KEY'], "Langsmith-Project": request['LANGSMITH_PROJECT']}
tp = TracerProvider(); tp.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers)))
trace_api.set_tracer_provider(tracer_provider=tp)
AgnoInstrumentor().instrument()
```

> Meka via `headers` och `endpoint`/OTLPSpanExporter; samma mönster för övriga OTel-beckends.
> Källa: docs.agno.com LangSmith-integrering (openinference-instrumentation-agno, metallic OTLP).

**LangWatch (enklast)**: SDK sköter OTel-konfiguration automatiskt.

```bash
uv pip install langwatch agno openai openinference-instrumentation-agno
export LANGWATCH_API_KEY=...
```

```python
import langwatch
from openinference.instrumentation.agno import AgnoInstrumentor
langwatch.setup(instrumentors=[AgnoInstrumentor()])   # sedan Autonormal agent
```

**Latitude (OSS, self-hostable → passar lokal-first)**: vanlig OTLP via env-var, self-hostad ingestion direkt.

```bash
uv pip install agno openai yfinance opentelemetry-sdk opentelemetry-exporter-otlp openinference-instrumentation-agno
export LATITUDE_API_KEY=... LATITUDE_PROJECT=...
# OTLP-exporteren appenderar /v1/traces till bas-URL
export OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.latitude.so   # eller egen self-hostad host
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer $LATITUDE_API_KEY,X-Latitude-Project=$LATITUDE_PROJECT"
```

```python
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

tp = TracerProvider(); tp.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
trace_api.set_tracer_provider(tracer_provider=tp)
AgnoInstrumentor().instrument()
# one-off-scripts: tracer_provider.shutdown() slutanmäler sista batch
```

## HITL (docs.agno.com/hitl/overview)

- Kapabilitet: "Pause runs for approval, input, or external execution".
- Approval-förfrågan → PWA-godkännandegrud (custom Dashboard, grilling #81: OT-vision + HITL).

## MCP (docs.agno.com/tools/mcp/overview)

- `from agno.tools.mcp import MCPTools`
- Koppla: `command=` (t.ex. `uvx mcp-server-git`) eller `url=` (streamable-http).
- Livscykel (rekommenderas): `await mcp_tools.connect()` … `finally: await mcp_tools.close()`.
- `refresh_connection=True`: uppdaterar/kör varje run (perf-nackdel, ej prod-default).
- `MultiMCPTools` för flera servrar; async-contextorm-namn som alternativ.
- Transporter: **stdio**, **Streamable HTTP** (och SSE) — subsidor `/tools/mcp/transports/{stdio,streamable-http,sse}`.
- Best practices: stäng alltid, felhantering på koppling/operationer, tydliga instructions.
- AgentOS hanterar MCP-kopplingar automatiskt (automatic connection management).
- Befintlig MCP-git-server (per ADR) ansluts här.

## AgentUI (OSS UI, AgentOS-visa)

- OSS Next.js/TS: `npx create-agent-ui@latest` (eller `git clone https://github.com/agno-agi/agent-ui`).
- `cd agent-ui && npm run dev` → `http://localhost:3006`, ange endpoint mot `http://localhost:8001`.
- "AgentOS only uses data in your database. No data is sent to Agno." — local-first-privacy lätt.
- **Används som referens/utgångspunkt, INTE som ersättare**: target = custom PWA (OT-vision + approval-UI), AgentUI + repos stilkopia för Annex.

## Byggordning (ticket #82)

1. `agno_agent.py`: Agent + 7 tools [] port + systemprompt; `SqliteDb`; remove OpenAI-/v1-routing.
2. Verktyg: porta tool-kropparna till agno-`@tool`.
3. HITL: approval-required känsliga verktyg + budget-guardrail/hook.
4. `main.py`/AgentOS: `AgentOS(agents=[...], mcp_server=True, tracing=True)`; server.py raderas.
5. PWA → AgentOS REST/SSE (chat, tool-cards, approvals).
6. Postgres+pgvector, durable/scheduler, MCP/ACP, OTel — post-MVP.

## Verifieringskriterier (klar = )

- Agent svarar via AgentOS-endpoint (`localhost:7777`) med lokal Ollama.
- HITL-approval pausar → godkänns → fortsätter.
- PWA-samtal fungerar (chat + tool-cards + approval-UI).

## Primärkällor

- Index: https://docs.agno.com/llms.txt
- SDK-översikt: https://docs.agno.com/sdk/setup · /agent-os/introduction
- MCP: https://docs.agno.com/tools/mcp/overview (+ transports, multiple-servers, dynamic-headers)
- HITL: https://docs.agno.com/hitl/overview
- AgentUI: `npx create-agent-ui@latest` / https://github.com/agno-agi/agent-ui