"""Prototype: HITL + provenans-logg (ADR 0006 §7/§8, ticket #48).

Agent foreslar, manniska godkanner konsekvens (AI Act art. 14). Varje
routingbeslut + hash av det skickade + modellversion loggas (AI Act art. 12).

Design (evidens fran docs/research/alert-fatigue.md):
- Risk-tiering: ENDAST hogrisk kraver HITL; lagrisk auto + audit.
- Konsekvensbaserad prompt + forcing function (motivering kravs for hogrisk).
- Rubber-stamp-detektering: godkannandegrad, beslutstidsdistribution,
  override-grad matas och flaggas (NIST/ENISA/Goddard).
- Provenanslogg innehaller aldrig remapping-tabell, rata hemligheter eller
  hela payloads -- bara hash + beslut + version.

ROUGH PROTOTYPE -- reaktionsunderlag, ej produktionskod.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field

MODEL_VERSION = "ollama:llama3.2"
FAST_DECISION_S = 2.0  # < 2 s godkannande flaggas som rubber-stamp-risk

HIGH_RISK_SENSITIVITIES = {"CONFIDENTIAL", "RESTRICTED"}


@dataclass
class ProvenanceEntry:
    event_id: str
    provenance_id: str
    actor: str  # agent | operator
    decision: str  # approved | rejected | auto_approved | override | denied
    reason: str
    ts: float
    model_version: str
    tier: str  # local | cloud
    sensitivity: str
    hash_sent: str  # sha256 av det skickade; ALDRIG innehållet
    decision_ms: int | None = None  # tid for manuellt beslut (rubber-stamp-matning)
    rubber_stamp_risk: bool = False


@dataclass
class HITLGate:
    provenance: list[ProvenanceEntry] = field(default_factory=list)
    approvals: int = 0
    rejections: int = 0
    overrides: int = 0
    auto_approved: int = 0
    _decision_times: list[float] = field(default_factory=list)

    def _log(self, *, actor: str, decision: str, reason: str, sensitivity: str,
             tier: str, payload: str, provenance_id: str, decision_ms: int | None = None,
             rubber_stamp_risk: bool = False) -> None:
        entry = ProvenanceEntry(
            event_id=f"ev-{len(self.provenance) + 1}",
            provenance_id=provenance_id,
            actor=actor,
            decision=decision,
            reason=reason,
            ts=time.time(),
            model_version=MODEL_VERSION,
            tier=tier,
            sensitivity=sensitivity,
            hash_sent=hashlib.sha256(payload.encode()).hexdigest()[:16],
            decision_ms=decision_ms,
            rubber_stamp_risk=rubber_stamp_risk,
        )
        self.provenance.append(entry)

    def request(self, *, action: str, consequence: str, sensitivity: str,
                tier: str = "local", payload: str, irreversible: bool = False) -> dict:
        """Agent foreslar en atgard. Returnerar om HITL kraevs (konsekvensbaserat)."""
        needs_hitl = sensitivity in HIGH_RISK_SENSITIVITIES or irreversible
        return {
            "needs_hitl": needs_hitl,
            "prompt": (
                f"AGENT: {action}\nKONSEKVENS: {consequence}\n"
                f"KANSLIGHET: {sensitivity} (tier {tier})\n"
                f"OKANSERLIGT: {irreversible}\n"
                "Godkanner du att detta utfors? (motivering kravs)"
            ),
        }

    def decide(self, *, request_id: str, operator: str, approve: bool, rationale: str,
               sensitivity: str, tier: str, payload: str, decision_ms: int) -> dict:
        """Operatorn fattar ett HITL-beslut med motivering (forcing function)."""
        self._decision_times.append(decision_ms)
        stamp_risk = decision_ms < FAST_DECISION_S * 1000
        decision = "approved" if approve else "rejected"
        if approve:
            self.approvals += 1
        else:
            self.rejections += 1
        self._log(
            actor=operator, decision=decision, reason=rationale, sensitivity=sensitivity,
            tier=tier, payload=payload, provenance_id=request_id,
            decision_ms=decision_ms, rubber_stamp_risk=stamp_risk,
        )
        return {
            "decision": decision,
            "rubber_stamp_risk": stamp_risk,
            "note": "FLAGGAD: for snabbt godkant (rubber-stamp-risk)" if stamp_risk else "ok",
        }

    def auto_approve(self, *, sensitivity: str, tier: str, payload: str,
                     provenance_id: str, reason: str = "lågrisk, automatisk + audit") -> None:
        """Lagrisk och reversibel: auto + full audit (sanker larmvolymen)."""
        self.auto_approved += 1
        self._log(actor="agent", decision="auto_approved", reason=reason,
                  sensitivity=sensitivity, tier=tier, payload=payload,
                  provenance_id=provenance_id)

    def override(self, *, provenance_id: str, recommendation: str, payload: str) -> None:
        """Operatorn overrider systemets rekommendation (override-matning)."""
        self.overrides += 1
        self._log(actor="operator", decision="override", reason=recommendation,
                  sensitivity="INTERNAL", tier="local", payload=payload,
                  provenance_id=provenance_id)

    def metrics(self) -> dict:
        n = len(self.provenance)
        total_manual = self.approvals + self.rejections
        approval_rate = round(100 * self.approvals / total_manual, 1) if total_manual else 0.0
        avg_ms = round(sum(self._decision_times) / len(self._decision_times), 0) if self._decision_times else 0
        fast = sum(1 for t in self._decision_times if t < FAST_DECISION_S * 1000)
        return {
            "approval_rate_pct": approval_rate,
            "override_count": self.overrides,
            "auto_approved": self.auto_approved,
            "avg_decision_ms": avg_ms,
            "fast_decisions_count": fast,
            "total_entries": n,
        }


def demo() -> None:
    gate = HITLGate()

    # 1) Lagrisk (INTERNAL): auto + audit, ingen HITL -> sänkt larmvolym.
    gate.auto_approve(sensitivity="INTERNAL", tier="local",
                      payload="normalisera accessloggar", provenance_id="prov-1")

    # 2) Hogrisk (CONFIDENTIAL re-grounding): kraver HITL, motivering.
    req = gate.request(
        action="re-grounda entitet vid egress",
        consequence="avslojar att identiteten ar SHALLOT-bricka-07 for operatorn",
        sensitivity="CONFIDENTIAL", payload="OT-tillgang ...", irreversible=True,
    )
    print("HITL prompt:", req["prompt"])
    # Operatorn klickar igenom pa 1.2 s -> rubber-stamp-flagg.
    r = gate.decide(request_id="prov-2", operator="anna", approve=True,
                    rationale="verifierad mot plats", sensitivity="CONFIDENTIAL",
                    tier="local", payload="OT-tillgang ...", decision_ms=1200)
    print("beslut:", r)

    # 3) Override: operatorn overrider en deny-rekommendation.
    gate.override(provenance_id="prov-3", recommendation="accepterar risk manuellt",
                  payload="falskt positiv larm")

    print("\n--- provenans (utdrag) ---")
    for e in gate.provenance:
        print(asdict(e))

    print("\n--- rubber-stamp-metrik ---")
    print(gate.metrics())


if __name__ == "__main__":
    demo()
