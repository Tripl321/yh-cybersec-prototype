"""Test configuration — ensure otel stub is loaded before any pydantic_ai import."""
from shallot_harness._otel_events_stub import *  # noqa: F401, F403
