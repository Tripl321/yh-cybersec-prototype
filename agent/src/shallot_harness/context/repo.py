"""Read-only filesystem context — directory tree, file listing."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class FileEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    size_bytes: int
    is_dir: bool


class RepoTree(BaseModel):
    model_config = ConfigDict(frozen=True)

    root: str
    entries: list[FileEntry]


class RepoContext:
    """Read-only view of a directory tree. No deps beyond stdlib."""

    def __init__(self, root_path: str, ignore: set[str] | None = None) -> None:
        self._root = Path(root_path)
        self._ignore = ignore or {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

    def tree(self, max_depth: int = 4) -> RepoTree:
        entries: list[FileEntry] = []
        self._walk(self._root, self._root, entries, 0, max_depth)
        return RepoTree(root=str(self._root), entries=entries)

    def _walk(self, base: Path, current: Path, entries: list[FileEntry], depth: int, max_depth: int) -> None:
        if depth >= max_depth:
            return
        try:
            for item in sorted(current.iterdir()):
                if item.name in self._ignore:
                    continue
                rel = item.relative_to(base)
                entries.append(
                    FileEntry(
                        path=str(rel),
                        size_bytes=item.stat().st_size if item.is_file() else 0,
                        is_dir=item.is_dir(),
                    )
                )
                if item.is_dir():
                    self._walk(base, item, entries, depth + 1, max_depth)
        except PermissionError:
            pass

    def read_file(self, rel_path: str) -> str:
        return (self._root / rel_path).read_text()

    def find(self, suffix: str) -> list[str]:
        return [str(p.relative_to(self._root)) for p in self._root.rglob(f"*{suffix}")]
