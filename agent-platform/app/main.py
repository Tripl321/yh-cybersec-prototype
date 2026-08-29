"""
AgentOS Entrypoint
==================
"""

from contextlib import asynccontextmanager
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from agno.os import AgentOS  # noqa: E402
from agno.utils.log import log_info  # noqa: E402

from agents.builder import platform_builder  # noqa: E402
from agents.engineer import platform_engineer  # noqa: E402
from agents.manager import platform_manager  # noqa: E402
from app.knowledge import shared_knowledge  # noqa: E402
from app.registry import registry  # noqa: E402
from app.schedules import register_schedules  # noqa: E402
from db import get_postgres_db  # noqa: E402
from teams.lead import agno_team  # noqa: E402
from workflows.deployment_check import deployment_check  # noqa: E402
from workflows.run_evals import run_evals  # noqa: E402

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
runtime_env = getenv("RUNTIME_ENV", "prd")
# Used by the scheduler and the OAuth server when MCP OAuth is enabled.
agentos_url = getenv("AGENTOS_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Interfaces
# - Agno becomes available on Slack when both env vars are set
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN = getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")

interfaces: list = []
if SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET:
    from agno.os.interfaces.slack import Slack

    interfaces.append(
        Slack(
            team=agno_team,
            streaming=True,
            token=SLACK_BOT_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET,
            resolve_user_identity=True,
            loading_text="Pulling the thread...",
        )
    )


# ---------------------------------------------------------------------------
# MCP OAuth — enabled by setting the MCP_CONNECT_SECRET environment variable.
# Connect your favorite AI apps and coding agents to a secure /mcp using OAuth.
# ---------------------------------------------------------------------------
MCP_CONNECT_SECRET = getenv("MCP_CONNECT_SECRET", "")

mcp_auth = None
if MCP_CONNECT_SECRET:
    from agno.os import AgentOSBuiltinAuth

    mcp_auth = AgentOSBuiltinAuth(
        url=agentos_url,
        secret=MCP_CONNECT_SECRET,
        signing_key_material=getenv("AGENTOS_MCP_SIGNING_KEY"),
    )


# ---------------------------------------------------------------------------
# Lifespan — app-level startup / teardown.
#
# AgentOS handles the MCP lifecycle (connect on startup, close on shutdown)
# for agent-attached and registry tools. Keep this hook to plug in your own setup.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    log_info("AgentOS lifespan: startup")
    # Register schedules on startup. Idempotent and fail-soft.
    register_schedules()
    try:
        yield
    finally:
        log_info("AgentOS lifespan: shutdown")


# ---------------------------------------------------------------------------
# Create AgentOS
# ---------------------------------------------------------------------------
agent_os = AgentOS(
    name="AgentOS",
    tracing=True,
    scheduler=True,
    scheduler_base_url=agentos_url,
    authorization=runtime_env != "dev",
    mcp_server=True,
    mcp_auth=mcp_auth,
    lifespan=lifespan,
    db=get_postgres_db(),
    knowledge=[shared_knowledge],
    agents=[platform_builder, platform_manager, platform_engineer],
    teams=[agno_team],
    workflows=[deployment_check, run_evals],
    interfaces=interfaces,
    registry=registry,
    config=str(Path(__file__).parent / "config.yaml"),
)
app = agent_os.get_app()


if __name__ == "__main__":
    agent_os.serve(app="app.main:app", reload=False)
