"""Tool registry for Cub (ADR 0005: explicit tool-allowlist).

Only tools registered here may be invoked by the agent.
"""
from __future__ import annotations


TOOL_REGISTRY: dict[str, str] = {
    "fido_ctap": "cub.tools.fido_ctap",
    "grc_siem": "cub.tools.grc_siem",
}


def allowed_tools() -> list[str]:
    return list(TOOL_REGISTRY)
