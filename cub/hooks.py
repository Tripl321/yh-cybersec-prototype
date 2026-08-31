"""
Tool hooks for the Cub agent (Agno) — local-first enforcement.

Maps ADR 0006 "Egress-verifiering" + "Provenans-logg" onto Agno tool
hooks: every tool call is intercepted to (1) log provenance (AI Act
art. 12 / GDPR 5(2)) and (2) deny egress by default (deny-by-default,
Tier 2 off unless --allow-cloud, ADR 0006 §6).

Deps: agno
"""

from agno.tools import FunctionCall, tool

# Tools that leave the perimeter. Deny by default; only allowed when Cub
# is started with explicit Tier-2 opt-in (--allow-cloud).
EGRESS_TOOLS = {"web_search", "http_request", "send_email", "fetch_url"}


def provenance_pre_hook(fc: FunctionCall) -> FunctionCall:
    # Pre-tool: record call for provenance log (AI Act art. 12).
    print(f"[provenance] pre  {fc.function.name}({fc.arguments})")
    if fc.function.name in EGRESS_TOOLS:
        # Default-deny egress; router never promotes to Tier 2 unprompted.
        raise PermissionError(
            f"tool '{fc.function.name}' is egress; blocked (deny-by-default). "
            "Enable Tier 2 explicitly with --allow-cloud."
        )
    return fc


def provenance_post_hook(fc: FunctionCall) -> FunctionCall:
    # Post-tool: record outcome in provenance log.
    print(f"[provenance] post {fc.function.name} -> {fc.result!r}")
    return fc


@tool(pre_hook=provenance_pre_hook, post_hook=provenance_post_hook)
def local_lookup(query: str) -> str:
    """Local-only lookup — passes the egress guard."""
    return f"local result for: {query}"
