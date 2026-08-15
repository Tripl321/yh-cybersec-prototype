"""Agentic memory + RAG (ADR 0006, component 9).

Local-only vector store (RAG) over framework docs / SHALLOT specs / runbooks /
historical findings, plus long-term episodic/semantic/procedural memory. Both
are local (zero egress), scrubbed on write, encrypted at rest, with TTL/purge
(GDPR minimization).
"""
from __future__ import annotations


class MemoryStore:
    def retrieve(self, query: str) -> list[str]:
        # TODO (RAG, #48/#49): local vector retrieval.
        return []

    def remember(self, event: str) -> None:
        # TODO: persist locally with TTL/purge (GDPR minimization).
        ...
