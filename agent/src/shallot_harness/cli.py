"""CLI entry point — starts SHALLOT Harness with Agno."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="SHALLOT Harness")
    parser.add_argument("--repo", default=".", help="Git repo path")
    parser.add_argument("--db", default="harness.db", help="SQLite DB path")
    parser.add_argument("--project", default="shallot", help="Project ID")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--model", default=None, help="Model override (e.g. ollama:qwen3:14b, ollama:qwen3-vl:8b, openai:gpt-4o)")
    args = parser.parse_args()

    from shallot_harness.agent import create_agent
    from shallot_harness.harness import Harness
    from shallot_harness.stub_reasoner import StubReasoner

    harness = Harness(
        project_id=args.project,
        repo_path=args.repo,
        db_path=args.db,
        reasoner=StubReasoner(),
    )

    agent = create_agent(harness, model=args.model)
    # Agno AgentOS provides UI/app; for CLI we start simple server
    # or expose Agno's AgentOS if available
    try:
        from agno.os import AgentOS

        agent_os = AgentOS(agents=[agent])
        app = agent_os.get_app()
        print(f"SHALLOT Harness (Agno AgentOS) — http://{args.host}:{args.port} (model {agent.model})")
        agent_os.serve(f"{args.host}:{args.port}")
    except Exception:
        # Fallback: use simple HTTP server
        import os

        os.environ["HARNESS_MODEL"] = args.model or "ollama:qwen3:14b"
        os.environ["HARNESS_PORT"] = str(args.port)
        os.environ["HARNESS_HOST"] = args.host
        from shallot_harness.server import main as server_main

        print(f"SHALLOT Harness — http://{args.host}:{args.port}")
        server_main()


if __name__ == "__main__":
    main()
