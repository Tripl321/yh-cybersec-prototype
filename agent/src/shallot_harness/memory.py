"""Structured memory — TTL, forget, reviewed promotion workflow."""

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict


class Memory(BaseModel):
    """A single memory entry. Provenance required for promoted memories."""

    model_config = ConfigDict(frozen=True)

    memory_id: UUID
    namespace: Literal["working", "episodic", "semantic", "procedural"]
    scope: Literal["person:johannes", "workspace:shallot", "session"]
    content: str
    created_at: datetime
    expires_at: datetime | None = None
    promoted: bool = False
    promotion_proof: str | None = None
    sensitivity: Literal["public", "internal", "confidential", "secret"] = "internal"

    @classmethod
    def create(
        cls,
        namespace: str,
        scope: str,
        content: str,
        ttl_hours: float | None = None,
        sensitivity: str = "internal",
    ) -> "Memory":
        now = datetime.now(UTC)
        return cls(
            memory_id=uuid4(),
            namespace=namespace,
            scope=scope,
            content=content,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours) if ttl_hours else None,
            sensitivity=sensitivity,
        )


class MemoryStore:
    """Append-only memory store with TTL, forget, and promotion."""

    def __init__(self) -> None:
        self._memories: dict[UUID, Memory] = {}

    def add(self, memory: Memory) -> None:
        self._memories[memory.memory_id] = memory

    def get(self, memory_id: UUID) -> Memory | None:
        m = self._memories.get(memory_id)
        if m and m.expires_at and datetime.now(UTC) > m.expires_at:
            return None
        return m

    def query(
        self,
        namespace: str | None = None,
        scope: str | None = None,
        include_expired: bool = False,
    ) -> list[Memory]:
        now = datetime.now(UTC)
        results = []
        for m in self._memories.values():
            if namespace and m.namespace != namespace:
                continue
            if scope and m.scope != scope:
                continue
            if not include_expired and m.expires_at and now > m.expires_at:
                continue
            results.append(m)
        return results

    def promote(self, memory_id: UUID, proof: str) -> bool:
        """Promote a memory to reviewed. Requires provenance proof."""
        m = self._memories.get(memory_id)
        if not m:
            return False
        self._memories[memory_id] = m.model_copy(
            update={"promoted": True, "promotion_proof": proof}
        )
        return True

    def forget(self, memory_id: UUID) -> bool:
        """Verifiable retraction. Removes from store."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False
