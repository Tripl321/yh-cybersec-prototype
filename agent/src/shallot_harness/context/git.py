"""Read-only Git context — branch, HEAD, dirty status, recent log."""

import subprocess
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GitCommit(BaseModel):
    model_config = ConfigDict(frozen=True)

    sha: str
    short_message: str
    author: str
    date: datetime


class GitState(BaseModel):
    model_config = ConfigDict(frozen=True)

    branch: str
    head_sha: str
    dirty: bool
    recent_commits: list[GitCommit]


class GitContext:
    """Read-only view of a git repository via subprocess."""

    def __init__(self, repo_path: str) -> None:
        self._path = repo_path

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", self._path, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def state(self, recent_n: int = 5) -> GitState:
        branch = self._run("rev-parse", "--abbrev-ref", "HEAD")
        head_sha = self._run("rev-parse", "HEAD")
        dirty = bool(self._run("status", "--porcelain"))
        log_output = self._run(
            "log", f"-{recent_n}", "--format=%H|%s|%an|%aI"
        )
        commits = []
        for line in log_output.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    GitCommit(
                        sha=parts[0],
                        short_message=parts[1],
                        author=parts[2],
                        date=datetime.fromisoformat(parts[3]),
                    )
                )
        return GitState(
            branch=branch,
            head_sha=head_sha,
            dirty=dirty,
            recent_commits=commits,
        )

    def diff_stat(self) -> str:
        return self._run("diff", "--stat")

    def file_content(self, path: str) -> str:
        return self._run("show", f"HEAD:{path}")
