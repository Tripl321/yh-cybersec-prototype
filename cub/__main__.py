"""Cub agent entry point.

Run:  python -m cub   (from repo root, with the project venv active)

Observability: Pydantic Logfire. Requires LOGFIRE_TOKEN (gitignored .env).
Without it, instrumentation is skipped and Cub still starts offline.
"""
from __future__ import annotations

import os

import logfire
from pydantic_ai import Agent

from cub.config import load_config
from cub.gateway import InferenceGateway
from cub.providers import build_local_model
from cub.tools import allowed_tools


def main() -> None:
    cfg = load_config()

    if os.environ.get("LOGFIRE_TOKEN"):
        logfire.configure()
        logfire.instrument_pydantic_ai()

    gateway = InferenceGateway(cfg)
    agent = build_local_model(cfg)  # constructed offline; no Ollama call at boot

    if os.environ.get("LOGFIRE_TOKEN"):
        logfire.info("cub.online", model=cfg.default_model)

    print(
        f"[cub] scaffold ready — model={cfg.default_model} "
        f"cloud={cfg.cloud_enabled} tools={allowed_tools()}"
    )


if __name__ == "__main__":
    main()
