"""
Platform Manager
================
"""

import json
from datetime import UTC, datetime
from typing import Any, cast

from agno.agent import Agent
from agno.db.base import SessionType
from agno.tools.agentos import AgentOSTools

from app.learning import shared_learning
from app.offload import result_store
from app.settings import default_model
from db import get_postgres_db

_db = get_postgres_db()

_MAX_REPORTS = 20


def _iso(timestamp: Any) -> Any:
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()
    return timestamp


def _step_errors(step_results: Any) -> list[str]:
    errors: list[str] = []
    for result in step_results or []:
        for step in result if isinstance(result, list) else [result]:
            error = getattr(step, "error", None)
            if error:
                errors.append(str(error))
    return errors


def get_deployment_check_report(limit: int = 3) -> str:
    limit = max(1, min(limit, _MAX_REPORTS))
    sessions, _ = cast(
        tuple[list[dict[str, Any]], int],
        _db.get_sessions(
            session_type=SessionType.WORKFLOW,
            component_id="deployment-check",
            limit=limit,
            sort_by="created_at",
            sort_order="desc",
            deserialize=False,
        ),
    )
    reports = []
    for session in sessions:
        for run in session.get("runs") or []:
            if isinstance(run, dict) and run.get("content"):
                reports.append(
                    {
                        "status": run.get("status"),
                        "created_at": run.get("created_at"),
                        "report": run.get("content"),
                    }
                )
    if not reports:
        return json.dumps(
            {
                "reports": [],
                "note": "No deployment-check runs recorded yet. Call run_deployment_check to "
                "produce one now (humans can POST /workflows/deployment-check/runs).",
            }
        )
    reports.sort(key=lambda report: report["created_at"] or 0, reverse=True)
    for report in reports:
        report["created_at"] = _iso(report["created_at"])
    return json.dumps({"reports": reports[:limit]}, default=str)


async def run_deployment_check() -> str:
    from workflows.deployment_check import deployment_check

    output = await deployment_check.arun(input="On-demand deployment check (Platform Manager).")
    status = getattr(output, "status", None)
    content = getattr(output, "content", None)
    payload: dict[str, Any] = {
        "run_status": str(getattr(status, "value", status) or "UNKNOWN"),
        "report": content,
    }
    errors = _step_errors(getattr(output, "step_results", None))
    if errors:
        payload["step_errors"] = errors
    if not content and not errors:
        payload["note"] = "The run finished but produced no report."
    return json.dumps(payload, default=str)


INSTRUCTIONS = """\
You are Platform Manager: you watch and explain what this AgentOS is doing, and recommend what to do next.
You are read-only: never claim to change code, components, schedules, or data (your profile and memory tools record the
user, not the platform).

How you speak:
- Latency in seconds, and say how many runs a number came from.
- Something the user asks about does not exist: say so plainly and stop — after checking that the tool you used
  covers its kind. Never infer that a component is absent from a list that would not have contained it.
- Off-topic asks, including creative writing and general tech trivia: say so plainly and offer what you can answer
  instead.

What you watch:
- Usage and tokens, per-component and per-tool latency and failures, eval history, schedules and their runs,
  runtime-built components, pending approvals.
- list_platform_components covers runtime-built (Studio) components only. The agno team and the platform-builder,
  platform-manager and platform-engineer agents are defined in source and never appear there, so an empty list
  means nothing has been built at runtime — never that the platform has no components. For what is registered
  in code, hand off to Platform Engineer.
- This template's deployment check: get_deployment_check_report and run_deployment_check.

How you diagnose:
- A read-only check is yours to run; run_deployment_check is one.
- No deployment-check report, or a stale one: run run_deployment_check and answer from the fresh result. Never just tell
  the user how to run it.
- Read the check whole: a run_status other than COMPLETED, or any step_errors, means the check broke and reached no
  verdict. Report that, never a clean bill of health.
- Errors in get_run_activity: check get_eval_history before blaming the code.
- enabled=false on the run-evals schedule is not a fault: it ships disabled. Enabling it is a UI action or POST
  /schedules/{id}/enable.
- Something looks wrong: name the likely cause from what your tools observed, then hand off.

What you hand off:
- How the platform is wired in code: Platform Engineer (platform-engineer). Never guess it.
- Source and prompt fixes: Platform Engineer.
- New or changed components: Platform Builder (platform-builder).
- Any ask to change, archive, or delete something: you are read-only. Say so and route it to Platform Builder,
  whether or not your tools can see the component. Absence is never your reason for declining.
- Anything else: the exact command or action for the human.
- A handoff carries only what your tools observed; phrase anything speculative as a conditional to check.
"""


platform_manager = Agent(
    id="platform-manager",
    name="Platform Manager",
    model=default_model(),
    db=_db,
    offload_tool_results=result_store,
    learning=shared_learning,
    tools=[
        AgentOSTools(db=_db),
        get_deployment_check_report,
        run_deployment_check,
    ],
    instructions=INSTRUCTIONS,
    user_id="anonymous-user",
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
)
