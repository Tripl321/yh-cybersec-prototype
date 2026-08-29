import subprocess
from datetime import UTC, datetime
from pathlib import Path

from shallot_harness.context.git import GitContext
from shallot_harness.context.repo import RepoContext


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True, check=True)


def test_git_state_returns_branch_and_head(tmp_path):
    _init_repo(tmp_path)
    ctx = GitContext(str(tmp_path))
    state = ctx.state()
    assert state.branch == "main"
    assert len(state.head_sha) == 40
    assert not state.dirty
    assert len(state.recent_commits) == 1
    assert state.recent_commits[0].short_message == "initial"


def test_git_detects_dirty(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "extra.txt").write_text("new")
    ctx = GitContext(str(tmp_path))
    assert ctx.state().dirty


def test_git_diff_stat(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "README.md").write_text("# updated")
    ctx = GitContext(str(tmp_path))
    stat = ctx.diff_stat()
    assert "README.md" in stat


def test_git_file_content(tmp_path):
    _init_repo(tmp_path)
    ctx = GitContext(str(tmp_path))
    assert ctx.file_content("README.md") == "# test"


def test_repo_tree_finds_files(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    (tmp_path / "b.py").write_text("y = 2")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("z = 3")

    ctx = RepoContext(str(tmp_path))
    tree = ctx.tree()
    paths = {e.path for e in tree.entries}
    assert "a.py" in paths
    assert "b.py" in paths
    assert "sub/c.py" in paths


def test_repo_tree_ignores_common_dirs(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("x")
    (tmp_path / "src.py").write_text("x")

    ctx = RepoContext(str(tmp_path))
    tree = ctx.tree()
    paths = {e.path for e in tree.entries}
    assert "src.py" in paths
    assert ".git/config" not in paths
    assert "node_modules/pkg.js" not in paths


def test_repo_tree_respects_max_depth(tmp_path):
    nested = tmp_path / "a" / "b" / "c" / "d"
    nested.mkdir(parents=True)
    (nested / "deep.txt").write_text("x")
    (tmp_path / "shallow.txt").write_text("x")

    ctx = RepoContext(str(tmp_path))
    tree = ctx.tree(max_depth=2)
    paths = {e.path for e in tree.entries}
    assert "shallow.txt" in paths
    assert "deep.txt" not in paths


def test_repo_find_by_suffix(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "b.py").write_text("y")
    (tmp_path / "c.txt").write_text("z")

    ctx = RepoContext(str(tmp_path))
    py_files = ctx.find(".py")
    assert sorted(py_files) == ["a.py", "b.py"]


def test_repo_read_file(tmp_path):
    (tmp_path / "hello.txt").write_text("world")
    ctx = RepoContext(str(tmp_path))
    assert ctx.read_file("hello.txt") == "world"
