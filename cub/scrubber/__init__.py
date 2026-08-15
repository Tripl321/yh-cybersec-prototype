"""Ingress Scrubber (ADR 0006).

Deterministic local FPE/hash of sensitive entities before they leave the
perimeter. Surrogate-encoded values are re-mapped locally; the remapping
table is excluded from the provenance log. Scrubbing runs regardless of the
sensitivity label (default-deny).
"""
from __future__ import annotations

from cub.config import CubConfig


class IngressScrubber:
    def __init__(self, cfg: CubConfig) -> None:
        self.cfg = cfg

    def scrub(self, text: str) -> str:
        # TODO (#38): deterministic FPE/hash over detected entities.
        return text
