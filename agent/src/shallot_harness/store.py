"""Append-only event store — protocol for backend swap (SQLite → PostgreSQL)."""

import sqlite3
from datetime import datetime
from typing import Protocol
from uuid import UUID

from shallot_harness.models import ProjectEvent, ProjectState, Provenance


class Store(Protocol):
    """Minimal append-only contract. PostgreSQL adds pgvector; this stays clean."""

    def append(self, event: ProjectEvent) -> None: ...
    def events(self, project_id: str) -> list[ProjectEvent]: ...
    def close(self) -> None: ...


class SQLiteStore:
    """SQLite implementation. Temporary — proves the seam while Docker is down."""

    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path, check_same_thread=False)
        _ = self._db.execute(
            """CREATE TABLE IF NOT EXISTS project_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                project_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                payload TEXT NOT NULL,
                provenance TEXT
            )"""
        )

    def append(self, event: ProjectEvent) -> None:
        _ = self._db.execute(
            "INSERT INTO project_events (event_id, project_id, kind, occurred_at, payload, provenance) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(event.event_id),
                event.project_id,
                event.kind,
                event.occurred_at.isoformat(),
                event.payload.model_dump_json(),
                event.provenance.model_dump_json() if event.provenance else None,
            ),
        )
        self._db.commit()

    def events(self, project_id: str) -> list[ProjectEvent]:
        rows = self._db.execute(
            "SELECT event_id, occurred_at, payload, provenance FROM project_events "
            "WHERE project_id = ? ORDER BY sequence ASC",
            (project_id,),
        ).fetchall()
        return [
            ProjectEvent(
                event_id=UUID(r[0]),
                kind="status.recorded",
                project_id=project_id,
                occurred_at=datetime.fromisoformat(r[1]),
                payload=ProjectState.model_validate_json(r[2]),
                provenance=Provenance.model_validate_json(r[3]) if r[3] else None,
            )
            for r in rows
        ]

    def close(self) -> None:
        self._db.close()
