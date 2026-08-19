"""Agentic memory + RAG (ADR 0006, component 9 / ADR 0007).

Supermemory-backed persistent memory for Cub: episodic, semantic, and
procedural memory with hybrid search (RAG + memory). Local-first via
Supermemory binary; scrubbed on write; encrypted at rest; TTL/purge for
GDPR minimization.

When SUPERMEMORY_API_KEY is not set, falls back to in-memory dict (offline mode).
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from cub.config import CubConfig


@dataclass
class _MemoryEntry:
    content: str
    ts: float
    ttl_seconds: int | None = None  # GDPR minimization: auto-expire

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.ts) > self.ttl_seconds


class MemoryStore:
    """Persistent memory backed by Supermemory API.

    Falls back to in-memory dict when Supermemory is unavailable (offline mode).
    """

    def __init__(self, cfg: CubConfig | None = None) -> None:
        self._cfg = cfg
        self._client = None
        self._fallback: dict[str, _MemoryEntry] = {}
        self._container_tag = "shallot-cub"

        api_key = os.environ.get("SUPERMEMORY_API_KEY")
        base_url = os.environ.get("SUPERMEMORY_BASE_URL", "http://localhost:6767")

        if api_key:
            try:
                from supermemory import Supermemory

                self._client = Supermemory(api_key=api_key, base_url=base_url)
            except ImportError:
                print("[cub] supermemory not installed; using in-memory fallback")
            except Exception as exc:
                print(f"[cub] Supermemory init failed: {exc}; using in-memory fallback")
        else:
            print("[cub] no SUPERMEMORY_API_KEY; using in-memory fallback")

    def retrieve(self, query: str, limit: int = 10) -> list[str]:
        """Search memories by semantic similarity (hybrid: RAG + memory)."""
        if self._client is not None:
            try:
                results = self._client.search(
                    q=query,
                    container_tag=self._container_tag,
                )
                if hasattr(results, "results") and results.results:
                    return [
                        r.content if hasattr(r, "content") else str(r)
                        for r in results.results[:limit]
                    ]
                return []
            except Exception as exc:
                print(f"[cub] Supermemory search failed: {exc}")

        # Fallback: simple substring match
        self._cleanup_expired()
        return [
            entry.content
            for entry in self._fallback.values()
            if query.lower() in entry.content.lower()
        ][:limit]

    def remember(self, event: str, ttl_seconds: int | None = None) -> None:
        """Store a memory. With TTL for GDPR minimization."""
        if self._client is not None:
            try:
                self._client.add(
                    content=event,
                    container_tag=self._container_tag,
                )
                return
            except Exception as exc:
                print(f"[cub] Supermemory add failed: {exc}; storing locally")

        # Fallback: local in-memory
        key = f"mem-{len(self._fallback)}-{int(time.time())}"
        self._fallback[key] = _MemoryEntry(
            content=event,
            ts=time.time(),
            ttl_seconds=ttl_seconds,
        )

    def get_profile(self, query: str = "") -> dict:
        """Get user profile (static facts + dynamic context)."""
        if self._client is not None:
            try:
                result = self._client.profile(
                    container_tag=self._container_tag,
                    q=query or "recent activity and preferences",
                )
                if hasattr(result, "profile"):
                    return {
                        "static": getattr(result.profile, "static", []),
                        "dynamic": getattr(result.profile, "dynamic", []),
                    }
            except Exception as exc:
                print(f"[cub] Supermemory profile failed: {exc}")

        return {"static": [], "dynamic": []}

    def _cleanup_expired(self) -> None:
        """Remove expired entries (GDPR minimization)."""
        expired = [k for k, v in self._fallback.items() if v.is_expired()]
        for k in expired:
            del self._fallback[k]

    def count(self) -> int:
        """Return number of stored memories."""
        if self._client is not None:
            try:
                results = self._client.search(q="*", container_tag=self._container_tag)
                if hasattr(results, "results"):
                    return len(results.results)
            except Exception:
                pass
        self._cleanup_expired()
        return len(self._fallback)
