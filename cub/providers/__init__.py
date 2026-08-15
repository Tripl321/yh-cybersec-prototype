"""Model providers (ADR 0006 tiers).

Tier 0: rules / classical ML (no LLM).
Tier 1: small local LLM via Ollama (default).
Tier 2: cloud LLM, opt-in only (runtime flag CUB_CLOUD_ENABLED=1).
"""
from __future__ import annotations

from cub.config import CubConfig


def build_local_model(cfg: CubConfig):
    import os
    from pydantic_ai import Agent
    # pydantic-ai's Ollama provider reads OLLAMA_BASE_URL; default it so the
    # agent boots offline without requiring the env var to be exported.
    os.environ.setdefault("OLLAMA_BASE_URL", cfg.ollama_base_url)
    return Agent(cfg.default_model)


def build_cloud_model(cfg: CubConfig):
    if not cfg.cloud_enabled or not cfg.cloud_model:
        raise RuntimeError("Tier 2 (cloud) is disabled by default (ADR 0006).")
    from pydantic_ai import Agent
    return Agent(cfg.cloud_model)
