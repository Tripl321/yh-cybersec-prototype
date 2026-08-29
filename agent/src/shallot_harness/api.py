"""FastAPI + AG-UI web interface for SHALLOT Harness."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from shallot_harness.harness import Harness

app = FastAPI(title="SHALLOT Harness", version="0.1.0")

_harness: Harness | None = None


class RunRequest(BaseModel):
    goal: str = "Continue SHALLOT prototype development"


class ApproveRequest(BaseModel):
    action_id: str


def init_harness(harness: Harness) -> None:
    global _harness
    _harness = harness


def _harness_or_503() -> Harness:
    if _harness is None:
        from fastapi import HTTPException
        raise HTTPException(503, "Harness not initialized")
    return _harness


@app.get("/api/state")
def get_state() -> dict:
    h = _harness_or_503()
    state = h.current_state()
    if state is None:
        return {"state": None}
    return {"state": state.model_dump()}


@app.post("/api/run")
def run_harness(req: RunRequest = RunRequest()) -> dict:
    h = _harness_or_503()
    result = h.run(goal=req.goal)
    return {
        "state": result["state"].model_dump(),
        "action": {
            "action_id": str(result["action"].action_id),
            "kind": result["action"].kind,
            "target": result["action"].target,
        },
        "verdict": result["verdict"].model_dump(),
    }


@app.get("/api/events")
def get_events(limit: int = 50) -> dict:
    h = _harness_or_503()
    events = h._ledger.events(h.project_id)
    return {
        "events": [
            {
                "event_id": str(e.event_id),
                "kind": e.kind,
                "occurred_at": e.occurred_at.isoformat(),
                "next_action": e.payload.next_action,
                "provenance": e.provenance.model_dump() if e.provenance else None,
            }
            for e in events[-limit:]
        ]
    }


@app.post("/api/approve")
def approve_action(req: ApproveRequest) -> dict:
    from uuid import UUID

    h = _harness_or_503()
    ok = h._policy.approve(UUID(req.action_id))
    return {"approved": ok}


@app.get("/api/memory")
def get_memory(namespace: str | None = None) -> dict:
    h = _harness_or_503()
    memories = h._memory.query(namespace=namespace)
    return {
        "memories": [
            {
                "memory_id": str(m.memory_id),
                "namespace": m.namespace,
                "scope": m.scope,
                "content": m.content,
                "promoted": m.promoted,
            }
            for m in memories
        ]
    }


@app.get("/", response_class=HTMLResponse)
def ui() -> str:
    return "<h1>SHALLOT Harness API</h1><p>Dashboard: <a href='/dashboard'>/dashboard</a></p>"
