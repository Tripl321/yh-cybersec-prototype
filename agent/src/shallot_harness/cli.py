"""CLI entry point — starts SHALLOT Harness with Pydantic AI web UI."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="SHALLOT Harness")
    parser.add_argument("--repo", default=".", help="Git repo path")
    parser.add_argument("--db", default="harness.db", help="SQLite DB path")
    parser.add_argument("--project", default="shallot", help="Project ID")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--model", default=None, help="Model override (e.g. ollama:llava, ollama:llama3.2, openai:gpt-4o)")
    args = parser.parse_args()

    from shallot_harness import _otel_events_stub  # noqa: F401 — ensure opentelemetry._events stub is loaded
    from shallot_harness.harness import Harness
    from shallot_harness.stub_reasoner import StubReasoner
    from shallot_harness.agent import create_agent

    harness = Harness(
        project_id=args.project,
        repo_path=args.repo,
        db_path=args.db,
        reasoner=StubReasoner(),
    )

    agent = create_agent(harness, model=args.model)
    app = agent.to_web()

    import uvicorn

    print(f"SHALLOT Harness — http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
