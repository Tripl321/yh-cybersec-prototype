"""Read-only context ingestion — git, GitHub, filesystem."""

from shallot_harness.context.git import GitContext, GitState, GitCommit
from shallot_harness.context.github import GitHubContext, GitHubIssue, GitHubPR
from shallot_harness.context.repo import RepoContext, RepoTree, FileEntry

__all__ = [
    "GitContext",
    "GitState",
    "GitCommit",
    "GitHubContext",
    "GitHubIssue",
    "GitHubPR",
    "RepoContext",
    "RepoTree",
    "FileEntry",
]
