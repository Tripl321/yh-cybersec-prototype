"""Stub for opentelemetry._events — auto-installs into sys.modules on import.

pydantic-ai 0.8.x imports opentelemetry._events which isn't in opentelemetry-api <=1.44.0.
Import this module early (before pydantic_ai) to install the shim.
Remove when opentelemetry-api >=1.45 lands on PyPI for Python 3.14.
"""
import sys
import types

_MODULE_NAME = "opentelemetry._events"

if _MODULE_NAME not in sys.modules:
    mod = types.ModuleType(_MODULE_NAME)

    class Event:
        pass

    class EventLogger:
        def emit(self, *args, **kwargs):
            pass

    class EventLoggerProvider:
        def get_event_logger(self, *args, **kwargs):
            return EventLogger()

    def get_event_logger_provider():
        return EventLoggerProvider()

    mod.Event = Event  # type: ignore[attr-defined]
    mod.EventLogger = EventLogger  # type: ignore[attr-defined]
    mod.EventLoggerProvider = EventLoggerProvider  # type: ignore[attr-defined]
    mod.get_event_logger_provider = get_event_logger_provider  # type: ignore[attr-defined]
    sys.modules[_MODULE_NAME] = mod
