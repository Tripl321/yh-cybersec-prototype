"""Inference Gateway (ADR 0006).

Internal protocol between Cub and tool/LLM providers. Enforces router policy,
scrubs ingress, verifies egress, and records provenance.
"""
from __future__ import annotations

from cub.config import CubConfig
from cub.router import Sensitivity, route
from cub.scrubber import IngressScrubber


class InferenceGateway:
    def __init__(self, cfg: CubConfig) -> None:
        self.cfg = cfg
        self.scrubber = IngressScrubber(cfg)

    def request(self, text: str, sensitivity: Sensitivity = Sensitivity.INTERNAL):
        scrubbed = self.scrubber.scrub(text)
        model = route(self.cfg, sensitivity)
        return model, scrubbed
