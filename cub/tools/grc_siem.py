"""Prototype: GRC / SIEM-logg / larm-verktyg for SHALLOT (ADR 0006 / #44).

Agentens verktyg ar tunna wrappers kring befintlig OSS:
- emission/instrumentering: OpenTelemetry -> lokal collector (localhost)
- lagring/fraga: lokal SIEM (Wazuh / Elastic / Loki+Promtail)
- detektion: Sigma-regler; ramverksmappning NIST CSF / SP 800-53 / MITRE / CIS
Prototypen anvander en lokal fil-sink som stallforetradare for OSS-stacken.

ROUGH PROTOTYPE -- reaktionsunderlag, ej produktionskod.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


SINK_PATH = Path(".cub/grc_events.jsonl")  # lokal sink (OTEL -> localhost SIEM)


@dataclass
class GrcEvent:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=time.time)
    actor: str = "agent"
    action: str = ""
    sensitivity: str = "INTERNAL"
    framework_tags: dict = field(default_factory=dict)  # {nist_csf, sp800_53, mitre, cis}
    outcome: str = ""
    provenance_id: str | None = None
    hitl_flag: bool = False


class GrcSink:
    """Lokal sink; i produktion OTEL-exporter till lokal SIEM-collector."""

    def __init__(self, path: Path = SINK_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: GrcEvent) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event)) + "\n")

    def query(self, *, tag: str | None = None, actor: str | None = None) -> list[dict]:
        out: list[dict] = []
        if not self.path.exists():
            return out
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            if tag and tag not in json.dumps(ev.get("framework_tags", {})):
                continue
            if actor and ev.get("actor") != actor:
                continue
            out.append(ev)
        return out


# --- Agent-verktyg (tunna wrappers kring OSS) ---


def emit_grc_event(
    action: str,
    *,
    framework_tags: dict,
    sensitivity: str = "INTERNAL",
    actor: str = "agent",
    provenance_id: str | None = None,
    hitl_flag: bool = False,
    outcome: str = "ok",
    sink: GrcSink | None = None,
) -> dict:
    ev = GrcEvent(
        action=action,
        framework_tags=framework_tags,
        sensitivity=sensitivity,
        actor=actor,
        provenance_id=provenance_id,
        hitl_flag=hitl_flag,
        outcome=outcome,
    )
    (sink or GrcSink()).append(ev)
    return {"ok": True, "event_id": ev.id}


def normalize_logs(raw: str) -> list[GrcEvent]:
    """Normaliserar demo/db.py + Flask-accessloggar till strukturerade handelser."""
    events: list[GrcEvent] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        events.append(
            GrcEvent(
                action="log",
                framework_tags={"nist_csf": ["DE.CM"]},
                sensitivity="INTERNAL",
                actor="system",
                outcome=line[:80],
            )
        )
    return events


def query_events(
    *,
    tag: str | None = None,
    actor: str | None = None,
    sink: GrcSink | None = None,
) -> list[dict]:
    return (sink or GrcSink()).query(tag=tag, actor=actor)


def triage_alarm(alarm: dict, *, sink: GrcSink | None = None) -> dict:
    """Larm-triage: klassificera via ramverksmappning (Sigma/ATT&CK i produktion)."""
    tags = alarm.get("framework_tags", {"mitre": ["T1078"]})
    ev = GrcEvent(
        action="triage",
        framework_tags=tags,
        sensitivity="RESTRICTED",
        actor="agent",
        outcome=alarm.get("summary", "unknown"),
    )
    (sink or GrcSink()).append(ev)
    return {"ok": True, "classified_tags": tags, "recommendation": "eskalera till HITL"}


# --- Allowlist-metadata (#44 Q4) ---
TOOL_METADATA: dict[str, dict] = {
    "emit_grc_event": {"sensitivity": "INTERNAL", "requires_metadata": ["provenance_id"]},
    "normalize_logs": {"sensitivity": "INTERNAL", "requires_metadata": []},
    "query_events": {"sensitivity": "INTERNAL", "requires_metadata": ["operator_scope"]},
    "triage_alarm": {"sensitivity": "RESTRICTED", "requires_metadata": ["provenance_id"]},
}


def demo() -> None:
    s = GrcSink()
    emit_grc_event(
        "register_credential",
        framework_tags={"sp800_53": ["AC-2"], "nist_csf": ["PR.AC"]},
        provenance_id="prov-1",
        sink=s,
    )
    for ev in normalize_logs("GET /api/login 200\nGET /api/register 403"):
        s.append(ev)
    print("query AC-2:", query_events(tag="AC-2", sink=s))
    print(
        "triage:",
        triage_alarm(
            {"summary": "flera misslyckade asserts", "framework_tags": {"mitre": ["T1078"]}},
            sink=s,
        ),
    )
    print("metadata:", TOOL_METADATA)


if __name__ == "__main__":
    demo()
