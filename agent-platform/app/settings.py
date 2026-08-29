"""App Settings
============

Shared runtime objects for the platform.
"""

from os import getenv

from agno.models.base import Model


def default_model() -> Model:
    """Fresh model instance per agent — avoids shared-state footguns.

    Local-first: Ollama against the Fedora control node by default.
    MODEL_PROVIDER=openai opts back in (judge evals / cloud runs).
    """
    if getenv("MODEL_PROVIDER", "ollama") == "openai":
        from agno.models.openai import OpenAIResponses

        return OpenAIResponses(id=getenv("OPENAI_MODEL", "gpt-5.6"))
    from agno.models.ollama import Ollama

    return Ollama(id=getenv("OLLAMA_MODEL", "ministral-3:8b"))
