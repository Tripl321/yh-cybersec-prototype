"""
Run Evals
=========

Workflow that runs a tagged subset of the eval suite and returns a compact report.
"""

import asyncio
from os import getenv

from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

from db import get_postgres_db

# Headroom per case for the setup and teardown hooks agno runs outside the per-case clock.
_HOOK_MARGIN_SECONDS = 30


def _int_env(name: str, default: int) -> int:
    value = getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _suite_timeout(selected: list, case_timeout: int) -> int:
    """The whole-suite ceiling, derived from the cases the tag actually selects.

    The per-case clock is the real limit; this one exists only to stop a run wedged
    *outside* it, because agno runs each case's setup and teardown outside the
    asyncio.wait_for that bounds the case. So the ceiling must never be tighter than the
    ceilings it contains. EVALS_SUITE_TIMEOUT_SECONDS still wins when set: an operator
    capping an unattended run's spend is making a different, deliberate trade.
    """
    override = _int_env("EVALS_SUITE_TIMEOUT_SECONDS", 0)
    if override > 0:
        return override
    ceilings = sum(case.timeout_seconds or case_timeout for case in selected)
    return max(ceilings + _HOOK_MARGIN_SECONDS * len(selected), 60)


def _one_line(text: str, limit: int = 400) -> str:
    """A judge verdict as one report line — reasons are prose and the report is a list."""
    collapsed = " ".join(str(text).split())
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 1] + "…"


def _failure_reasons(case: dict) -> list[str]:
    """Why a case failed, from the payload alone."""
    reasons: list[str] = []
    if case.get("error"):
        reasons.append(_one_line(case["error"]))
    if case.get("judge_passed") is False:
        reasons.append(f"judge: {_one_line(case.get('judge_reason') or 'no reason recorded')}")
    if case.get("score_passed") is False:
        reasons.append(f"scorer: {_one_line(case.get('score_reason') or 'no reason recorded')}")
    if case.get("reliability_passed") is False:
        fired = ", ".join(case.get("tools_called") or []) or "none"
        reasons.append(f"reliability: expected tool calls missing; fired {fired}")
    return reasons


def _case_lines(payload: dict) -> list[str]:
    lines: list[str] = []
    for case in payload.get("cases", []):
        result = "PASS" if case.get("passed") else "FAIL"
        detail = f"{result} `{case.get('name')}` ({case.get('duration_seconds', 0)}s)"
        reasons = _failure_reasons(case)
        if reasons:
            detail += " — " + "; ".join(reasons)
        lines.append(f"- {detail}")
    return lines


def _format_summary(payload: dict) -> str:
    summary = payload.get("summary", {})
    status = summary.get("status", "FAIL")
    lines = [
        "# Evals",
        "",
        f"Overall: **{status}** ({summary.get('passed', 0)}/{summary.get('total', 0)} passed)",
        "",
    ]
    lines.extend(_case_lines(payload))
    return "\n".join(lines)


def _format_timeout(payload: dict, *, tag: str, limit: int, selected: int, stuck: str | None) -> str:
    """The suite ran out of clock — report what finished rather than only that it did."""
    summary = payload.get("summary", {})
    stalled = f", with `{stuck}` still running" if stuck else ""
    lines = [
        "# Evals",
        "",
        f"Overall: **FAIL** — the `{tag}` suite exceeded {limit}s (EVALS_SUITE_TIMEOUT_SECONDS){stalled}.",
        "",
        f"{summary.get('total', 0)}/{selected} cases finished first ({summary.get('passed', 0)} passed):",
        "",
    ]
    lines.extend(_case_lines(payload) or ["- (no case finished)"])
    return "\n".join(lines)


async def run_evals_step(_step_input: StepInput) -> StepOutput:
    """Run the configured eval tag in-process and return a markdown summary."""
    # Imported lazily so the eval suite only loads when the workflow actually runs.
    from agno.eval import SuiteResult, arun_cases

    from evals.cases import CASES, eval_db

    tag = getenv("EVALS_TAG", "smoke")
    case_timeout_seconds = _int_env("EVALS_CASE_TIMEOUT_SECONDS", 90)
    selected = [case for case in CASES if tag in case.tags]
    suite_timeout_seconds = _suite_timeout(selected, case_timeout_seconds)

    # arun_cases hands each result to on_case_end as it lands, which is the only way to
    # keep any of them when the suite clock expires.
    finished: list = []
    started: list[str] = []

    try:
        suite = await asyncio.wait_for(
            arun_cases(
                CASES,
                tag=tag,
                default_timeout=case_timeout_seconds,
                db=eval_db,
                on_case_start=lambda case: started.append(case.name),
                on_case_end=lambda case, result: finished.append(result),
            ),
            timeout=suite_timeout_seconds,
        )
    except TimeoutError:
        return StepOutput(
            content=_format_timeout(
                SuiteResult(results=finished).to_dict(),
                tag=tag,
                limit=suite_timeout_seconds,
                selected=len(selected),
                # One name is in flight exactly when a case started and has not landed.
                stuck=started[-1] if len(started) > len(finished) else None,
            ),
            success=False,
        )

    return StepOutput(
        content=_format_summary(suite.to_dict()),
        success=suite.status == "PASS",
    )


run_evals = Workflow(
    id="run-evals",
    name="Run Evals",
    db=get_postgres_db(),
    steps=[Step(name="run-evals", executor=run_evals_step)],
)
