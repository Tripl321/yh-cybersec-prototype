"""Cub — the SHALLOT LLM agent.

Local-first inference architecture (ADR 0006): tiers 0/1 local, tier 2 cloud
opt-in; ingress scrubber; model router/PDP; inference gateway; agentic
memory + RAG; egress verification; HITL; provenance logging.

Scaffolded under ticket #37.
"""
__version__ = "0.1.0"
