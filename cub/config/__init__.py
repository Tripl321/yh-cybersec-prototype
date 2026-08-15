"""Runtime configuration for Cub (ADR 0005 / ADR 0006)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CubConfig:
    # Local-first: default to a small local Ollama model (tier 1).
    # The "ollama:" prefix selects the Ollama provider; base URL is below.
    default_model: str = "ollama:llama3.2"
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    # Cloud opt-in is OFF by default (ADR 0006 — Tier 2 runtime flag).
    cloud_enabled: bool = os.environ.get("CUB_CLOUD_ENABLED", "0") == "1"
    cloud_model: str | None = os.environ.get("CUB_CLOUD_MODEL")

    # Ingress scrubber (FPE key, local + deterministic).
    scrubber_fpe_key: str | None = os.environ.get("CUB_SCRUBBER_KEY")

    # Provenance log path (remapping table is excluded from this log).
    provenance_log: str = os.environ.get("CUB_PROVENANCE_LOG", "cub-provenance.log")


def load_config() -> CubConfig:
    return CubConfig()
