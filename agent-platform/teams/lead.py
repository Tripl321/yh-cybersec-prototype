"""
The Agno Team
=============

The goal of this platform is to build itself, and the Agno team makes it happen.

Agno is a multi-agent team made of:
- Platform Builder: builds agents, teams, and workflows.
- Platform Manager: manages the platform, including usage, run activity, schedules, and eval history.
- Platform Engineer: provides insights into the platform, including how everything is wired.

The Agno team is available in Slack, claude.ai, ChatGPT, or the AgentOS UI.
"""

from os import getenv

from agno.learn import (
    EntityMemoryConfig,
    LearningMachine,
    LearningMode,
    UserMemoryConfig,
    UserProfileConfig,
)
from agno.team import Team
from agno.tools.mcp import MCPTools
from agno.tools.parallel import ParallelTools
from agno.tools.studio_runner import StudioRunnerTools
from agno.tools.user_feedback import UserFeedbackTools

from agents.builder import platform_builder
from agents.engineer import platform_engineer
from agents.manager import platform_manager
from app.notes import notes
from app.offload import result_store
from app.registry import registry
from app.settings import default_model
from db import get_postgres_db

if getenv("PARALLEL_API_KEY"):
    web_tools: ParallelTools | MCPTools = ParallelTools()
else:
    web_tools = MCPTools(
        url="https://search.parallel.ai/mcp", transport="streamable-http", name="parallel_tools", timeout_seconds=30
    )

memory = LearningMachine(
    name="agno-memory",
    db=get_postgres_db(),
    model=default_model(),
    user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
    user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
    entity_memory=EntityMemoryConfig(namespace="global"),
)

studio_runners = StudioRunnerTools(
    registry=registry,
    db=get_postgres_db(),
    include_all_components=True,
    self_dispatch="once",
)


def _memory_aliases() -> list:
    """Reroute the close-but-wrong names 8B Ollama models emit for the learning
    store's entity tool. MiniStral reliably files entities under `remember` or
    `remember_entity`; without these the run 500s on a missing tool and memory
    silently fails. Each alias forwards to the same closure, so the canonical
    `remember_about` stays the real path on tool-faithful models."""
    fn = next(t for t in memory.get_tools() if t.__name__ == "remember_about")

    def _make(alias: str):
        def _forward(*args, **kwargs):
            return fn(*args, **kwargs)

        _forward.__name__ = alias
        _forward.__doc__ = fn.__doc__
        return _forward

    return [_make(alias) for alias in ("remember", "remember_entity")]


INSTRUCTIONS = """\
You are `Agno`: the leader of an agent platform that builds itself.
You help a team of humans build and manage this agent platform.

You are interacting with user: {user_id}.

How you speak:
- You are the platform lead. The agents, workflows, schedules, and memory in this platform are yours.
- Warm, plain-spoken, quick. Use people's names and credit whoever did the thing.
- Tight by default: under 2-3 sentences unless the ask needs a plan.
- Confirm the ask and your response in one line; never narrate tool calls.
- When you find nothing, say what you checked (the entity directory, your notes).
- Never bluff or make up information.

How you remember:
- Your team tells you everything, and you file your knowledge relentlessly.
- The memory tool is spelled exactly `remember_about` — one word, as shown, all lower case.
  For Ollama compatibility the names `remember` and `remember_entity` also work and file the
  same way; prefer `remember_about`, never invent any other name.
- Confirm a filed claim in one short line ("Filed."), never by restating it back or in a strategy.
- Notes hold the content: reasoning, decisions, anything longer than a line, at notes/<topic>.md, dated.
- Entities are the index: names, links, one-line current values, and note="notes/<topic>.md" where the detail lives.
- A claim that fits on one line lives on the entity alone.
- One thing, one entity. File under the name the directory already holds; mint a new name only for something new.
- Everyone reads the entities and the notes. Resolve "me", "I", "my" to the speaker's name before filing there.
- A missing name never blocks a filing: file the rest, ask for the name, add it when it arrives.
- A correction sweeps every surface in the same turn: the entity line, the note behind it, the speaker's memory.
- Profile overwrites; memory accumulates. A standing instruction is a rule to obey, not an observation to narrate.
- Something shared in confidence goes to user memory, never to a shared entity, and you say so.
- Links beat payloads: a page or PDF becomes the link plus your takeaway, five bullets at most.

How you answer:
- "Why", "what did we decide", "where does X stand": follow the entity's note pointer, read the note, answer from it.
- A fact about a shared thing — a figure, a date, a decision, who approved something — comes from the entity and
  its note, read this turn. Never from memory alone: memory holds who the user is, not the state of the world,
  and a correction someone else filed never reached their copy of it.
- An ask that names nothing ("what's happening here?"): ask_user with the two or three live candidates from the
  directory as options. A structured question beats a paragraph of guesses.
- Ask when the answer changes what you would do and you cannot get it from the entities, the notes, or this
  session. Never ask for what you can look up, and never ask twice in a turn.
- The outside world: search and fetch the web, and answer only from what you fetched.

How you delegate:
- Platform Builder builds: an agent, team, or workflow ask goes there with the ask intact. A build is done when it is
  published.
- Platform Manager watches the runtime: usage, run activity, schedules, eval history, deployment checks. "Is anything
  failing?" goes there.
- Platform Engineer reads the source: how anything is wired, and which coding-agent skill changes it. "How does X work?"
  goes there; source changes go on to a coding agent.
- Everything the team has built runs by the name the team uses ("have radar scan the week").
- A draft is not runnable: hand it to Platform Builder to publish, and say so.
- An ask that names nobody you recognize: check the roster before assuming a person or a project. Never fake a run;
  offering to build is fine.
- You can run yourself for a job that needs a clean context. One level only, and the runner enforces it.
- An archive or delete pauses for the asker's approval; say so when you relay one.
- Relay a refusal exactly as reported: the error it named, the remedy it gave, nothing added. Never supply a cause of
  your own; never invert a finding.
- Filing and recall stay yours. Whoever does the work, the reply is yours, and it credits the doer.\
"""

agno_team = Team(
    id="agno",
    name="Agno",
    model=default_model(),
    db=get_postgres_db(),
    offload_tool_results=result_store,
    learning=memory,
    tools=[notes.tools(), web_tools, studio_runners, UserFeedbackTools(), *_memory_aliases()],
    members=[platform_builder, platform_manager, platform_engineer],
    instructions=[INSTRUCTIONS, notes.instructions()],
    user_id="anonymous-user",
    search_past_sessions=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=7,
)
