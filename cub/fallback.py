"""
Local-first fallback models (Agno) for the Cub agent.

Adapted from Agno cookbook 01_basic_fallback. ADR 0006 keeps inference
local (Tier 1 Ollama); a cloud fallback would break zero-egress, so the
secondary is also a local Ollama model. Pull both before running.

Deps: agno ollama
"""

from agno.agent import Agent
from agno.models.ollama import Ollama

# Primary + local fallback. Same model as fallback is pointless; use a
# second locally-pulled model (e.g. `ollama pull qwen2.5`).
agent = Agent(
    model=Ollama(id="llama3.2", retries=2),
    fallback_models=[Ollama(id="qwen2.5")],
)


if __name__ == "__main__":
    agent.print_response("What is the meaning of life?", stream=True)
