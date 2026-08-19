"""GRC / SIEM-logg / larm-verktyg for SHALLOT (ADR 0006 / ADR 0007 / #44).

Agentens verktyg ar tunna wrappers kring Wazuh SIEM:
- emission/instrumentering: Wazuh API (POST /events)
- lagring/fraga: Wazuh indexer (Elasticsearch-compatible)
- detektion: Sigma-regler; ramverksmappning NIST CSF / SP 800-53 / MITRE / CIS

Fallback: lokal JSONL-fil nar Wazuh API ej ar tillgangligt (offline/labbet).
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

import requests


SINK_PATH = Path(".cub/grc_events.jsonl")

# Wazuh API config (ADR 0007)
WAZUH_API_URL = os.environ.get("WAZUH_API_URL", "")  # e.g. https://localhost:55000
WAZUH_API_TOKEN = os.environ.get("WAZUH_API_TOKEN", "")  # Bearer token
WAZUH_VERIFY_SSL = os.environ.get("WAZUH_VERIFY_SSL", "0") == "1"  # self-signed certs


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
    """Wazuh-backed SIEM sink with JSONL fallback.

    When WAZUH_API_URL is set, events are sent to Wazuh API.
    Otherwise, falls back to local JSONL file (offline/labbet).
    """

    def __init__(self, path: Path = SINK_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._wazuh_available = bool(WAZUH_API_URL and WAZUH_API_TOKEN)
        self._session: requests.Session | None = None

        if self._wazuh_available:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {WAZUH_API_TOKEN}",
                "Content-Type": "application/json",
            })

    def append(self, event: GrcEvent) -> None:
        """Send event to Wazuh or fallback to JSONL."""
        if self._wazuh_available and self._session is not None:
            try:
                payload = {
                    "event": asdict(event),
                    "rule": {
                        "groups": ["shallot", event.sensitivity.lower()],
                        "level": self._severity_to_level(event.sensitivity),
                    },
                    "agent": {
                        "id": "cub-agent",
                        "name": "shallot-cub",
                    },
                    "location": f"cub.{event.action}",
                }
                resp = self._session.post(
                    f"{WAZUH_API_URL}/events",
                    json=payload,
                    verify=WAZUH_VERIFY_SSL,
                    timeout=5,
                )
                resp.raise_for_status()
                return
            except Exception as exc:
                print(f"[cub] Wazuh API append failed: {exc}; falling back to JSONL")

        # Fallback: local JSONL
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event)) + "\n")

    def query(self, *, tag: str | None = None, actor: str | None = None) -> list[dict]:
        """Query events from Wazuh or fallback to JSONL."""
        if self._wazuh_available and self._session is not None:
            try:
                query_body: dict = {"query": {"bool": {"must": []}}}
                if tag:
                    query_body["query"]["bool"]["must"].append(
                        {"match": {"event.framework_tags": tag}}
                    )
                if actor:
                    query_body["query"]["bool"]["must"].append(
                        {"term": {"event.actor": actor}}
                    )
                if not query_body["query"]["bool"]["must"]:
                    query_body = {"query": {"match_all": {}}}

                resp = self._session.post(
                    f"{WAZUH_API_URL}/events/_search",
                    json=query_body,
                    verify=WAZUH_VERIFY_SSL,
                    timeout=10,
                )
                resp.raise_for_status()
                hits = resp.json().get("hits", {}).get("hits", [])
                return [h.get("_source", {}).get("event", {}) for h in hits]
            except Exception as exc:
                print(f"[cub] Wazuh API query failed: {exc}; falling back to JSONL")

        # Fallback: local JSONL
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

    def healthcheck(self) -> dict:
        """Check Wazuh API connectivity."""
        if not self._wazuh_available or self._session is None:
            return {"status": "offline", "fallback": "jsonl"}
        try:
            resp = self._session.get(
                f"{WAZUH_API_URL}/",
                verify=WAZUH_VERIFY_SSL,
                timeout=5,
            )
            resp.raise_for_status()
            return {"status": "online", "wazuh_version": resp.json().get("api_version", "unknown")}
        except Exception as exc:
            return {"status": "error", "error": str(exc), "fallback": "jsonl"}

    @staticmethod
    def _severity_to_level(sensitivity: str) -> int:
        """Map SHALLOT sensitivity to Wazuh rule level (0-15)."""
        return {
            "CONFIDENTIAL": 12,
            "RESTRICTED": 15,
            "INTERNAL": 5,
            "PUBLIC": 2,
        }.get(sensitivity, 5)


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
    print("healthcheck:", s.healthcheck())
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
