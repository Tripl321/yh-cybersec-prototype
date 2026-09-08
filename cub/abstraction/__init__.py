"""Prototype: lokal abstraktion/generalisering (ADR 0006 §2/§5).

Syfte: lokal modell ska aldrig se ett konkret förlopp — den får en generaliserad
hypotetisk fråga ("Ponera att ..."). Re-grounding vänder tillbaka till konkret
kontext vid egress (via samma surrogat-map som scrubbern, #38).

ROUGH PROTOTYPE — reaktionsunderlag, inte produktionskod.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    asset: str
    time: str
    asserts_failed: int
    window_min: int
    watched: bool


# Enkel surrogat-map (i verkligheten från scrubbern, #38). Hårdkodad för demo.
_SURROGATES = {"SHALLOT-bricka-07": "OT-tillgång"}


def _surrogatize(text: str) -> str:
    for real, surr in _SURROGATES.items():
        text = text.replace(real, surr)
    return text


def _reground(text: str) -> str:
    for real, surr in _SURROGATES.items():
        text = text.replace(surr, real)
    return text


def abstract(event: Event) -> str:
    """Formulerar generaliserad hypotetisk fråga — minimal läcka: entitet, antal,
    tidsfönster och tidpunkt generaliseras till vaga termer. Inget konkret lämnar."""
    asset = _SURROGATES.get(event.asset, "OT-tillgång")
    watched = "bevakat" if event.watched else "obevakat"
    text = (
        f"{asset} fick flera misslyckade asserts under en kort tid "
        f"vid ett {watched} tillfälle."
    )
    return (
        "Ponera att en " + text
        + " Vad indikerar detta generellt, och vilka åtgärder är lämpliga?"
    )


def local_model_respond(prompt: str) -> str:
    """Mock av lokal modell — svarar på den generaliserade frågan, hypotetiskt."""
    return (
        "Flera misslyckade asserts på kort tid hos en OT-tillgång under ett "
        "obevakat fönster indikerar troligen återkommande autentiserings- eller "
        "orienteringsproblem. Lämpliga åtgärder: granska tillgångens senaste "
        "nyckelrotation, verifiera fysisk närvarodetektering, och eskalera till "
        "HITL om mönstret upprepas."
    )


def reground(answer: str, to_concrete: bool = True) -> str:
    """Vänder tillbaka till konkret kontext vid egress (om tillåtet)."""
    return _reground(answer) if to_concrete else answer


def demo() -> None:
    ev = Event("SHALLOT-bricka-07", "2026-08-15 03:14", 5, 12, False)
    prompt = abstract(ev)
    print("--- lokal modell ser (generaliserat) ---")
    print(prompt)
    ans = local_model_respond(prompt)
    print("\n--- modell-svar (generaliserat) ---")
    print(ans)
    print("\n--- re-grounded till operatör (egress) ---")
    print(reground(ans))


if __name__ == "__main__":
    demo()
