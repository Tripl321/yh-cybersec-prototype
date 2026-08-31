"""SHALLOT Harness server — AgentOS runtime."""

import os

from agno.os import AgentOS
from shallot_harness.agent import create_agent
from shallot_harness.harness import Harness
from shallot_harness.stub_reasoner import StubReasoner

MODEL = os.environ.get("HARNESS_MODEL", "ollama:qwen3:14b")
DATA_DIR = os.environ.get("HARNESS_DATA", os.path.join(os.path.dirname(__file__), "..", "harness_data"))
os.makedirs(DATA_DIR, exist_ok=True)

_harness = Harness(
    "shallot",
    os.environ.get("HARNESS_REPO", os.getcwd()),
    os.path.join(DATA_DIR, "harness.db"),
    StubReasoner(),
)
_agent = create_agent(_harness, model=MODEL)

agent_os = AgentOS(
    agents=[_agent],
    cors_allowed_origins=["http://localhost:3005", "http://localhost:3006"],
)
app = agent_os.get_app()


def main() -> None:
    host = os.environ.get("HARNESS_HOST", "0.0.0.0")
    port = int(os.environ.get("HARNESS_PORT", "8001"))
    print(f"SHALLOT Harness server on {host}:{port} (model {MODEL})")
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
