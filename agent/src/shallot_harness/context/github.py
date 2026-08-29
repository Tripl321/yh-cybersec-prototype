"""Read-only GitHub context via gh CLI."""

import json
import subprocess
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GitHubIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    title: str
    state: str
    labels: list[str]
    created_at: datetime
    updated_at: datetime


class GitHubPR(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    title: str
    state: str
    head_ref: str
    base_ref: str


class GitHubContext:
    """Read-only view of a GitHub repo via gh CLI."""

    def __init__(self, repo_path: str) -> None:
        self._path = repo_path

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=self._path,
        )
        if result.returncode != 0:
            raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def _try_run(self, *args: str) -> str | None:
        try:
            return self._run(*args)
        except RuntimeError:
            return None

    def issues(self, state: str = "open", limit: int = 20) -> list[GitHubIssue]:
        raw = self._try_run(
            "issue", "list",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,state,labels,createdAt,updatedAt",
        )
        if not raw:
            return []
        items = json.loads(raw)
        return [
            GitHubIssue(
                number=i["number"],
                title=i["title"],
                state=i["state"],
                labels=[l["name"] for l in i["labels"]],
                created_at=datetime.fromisoformat(i["createdAt"]),
                updated_at=datetime.fromisoformat(i["updatedAt"]),
            )
            for i in items
        ]

    def prs(self, state: str = "open", limit: int = 20) -> list[GitHubPR]:
        raw = self._try_run(
            "pr", "list",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,state,headRefName,baseRefName",
        )
        if not raw:
            return []
        items = json.loads(raw)
        return [
            GitHubPR(
                number=i["number"],
                title=i["title"],
                state=i["state"],
                head_ref=i["headRefName"],
                base_ref=i["baseRefName"],
            )
            for i in items
        ]

    def issue_body(self, number: int) -> str:
        return self._run("issue", "view", str(number), "--json", "body", "--jq", ".body")
