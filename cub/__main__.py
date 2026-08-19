"""Cub agent entry point.

Run:  python -m cub   (from repo root, with the project venv active)

Observability: Latitude (MIT). Requires LATITUDE_API_KEY + LATITUDE_PROJECT_SLUG
(gitignored .env). Without them, instrumentation is skipped and Cub still starts
offline.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from pydantic_ai import Agent

from cub.config import load_config
from cub.gateway import InferenceGateway
from cub.providers import build_local_model
from cub.tools import allowed_tools

_latitude = None


def _init_latitude():
    """Initialize Latitude telemetry if API key is present."""
    global _latitude
    api_key = os.environ.get("LATITUDE_API_KEY")
    project = os.environ.get("LATITUDE_PROJECT_SLUG", "shallot")
    if not api_key:
        return None
    try:
        import ollama as _ollama_mod
        from latitude_telemetry import Latitude

        _latitude = Latitude(
            api_key=api_key,
            project=project,
            instrumentations={"ollama": _ollama_mod},
        )
        return _latitude
    except ImportError:
        print("[cub] latitude-telemetry not installed; skipping observability")
        return None
    except Exception as exc:
        print(f"[cub] Latitude init failed: {exc}")
        return None


@contextmanager
def _trace(operation: str, **kwargs) -> Iterator[None]:
    """Wrap an operation in a Latitude trace if available."""
    if _latitude is not None:
        try:
            from latitude_telemetry import capture

            with capture(operation, lambda: None, kwargs):
                yield
            return
        except Exception:
            pass
    yield


def main() -> None:
    cfg = load_config()

    _init_latitude()

    gateway = InferenceGateway(cfg)
    agent = build_local_model(cfg)  # constructed offline; no Ollama call at boot

    if _latitude is not None:
        print(f"[cub] Latitude tracing active — model={cfg.default_model}")

    print(
        f"[cub] scaffold ready — model={cfg.default_model} "
        f"cloud={cfg.cloud_enabled} tools={allowed_tools()}"
    )


def shutdown() -> None:
    """Flush and shut down Latitude telemetry."""
    if _latitude is not None:
        try:
            _latitude.flush()
            _latitude.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()
