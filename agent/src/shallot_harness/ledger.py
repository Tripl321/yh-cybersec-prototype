"""ProjectLedger — replays events to reconstruct canonical ProjectState."""

from shallot_harness.models import ProjectEvent, ProjectState
from shallot_harness.store import SQLiteStore, Store


class ProjectLedger:
    """Append-only ledger. State is derived by replaying events from any Store backend."""

    def __init__(self, path: str, store: Store | None = None) -> None:
        self._store = store or SQLiteStore(path)

    def append(self, event: ProjectEvent) -> None:
        self._store.append(event)

    def state(self, project_id: str) -> ProjectState | None:
        """Reconstruct latest state by replaying events. No stored state needed."""
        events = self._store.events(project_id)
        if not events:
            return None
        return events[-1].payload

    def events(self, project_id: str) -> list[ProjectEvent]:
        return self._store.events(project_id)

    def close(self) -> None:
        self._store.close()
