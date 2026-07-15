"""Layer 1: Filesystem path sandbox."""
from pathlib import Path
from harness.models import GuardResult, GuardAction


class PathSandbox:
    """Restrict file read/write to allowed directories."""

    def __init__(self, root: str | Path):
        self._root = Path(root).resolve()
        self._writable_dirs: set[Path] = {self._root}
        self._readable_dirs: set[Path] = {self._root}

    def add_writable_dir(self, path: Path):
        self._writable_dirs.add(path.resolve())

    def add_readable_dir(self, path: Path):
        self._readable_dirs.add(path.resolve())

    def validate(self, path_str: str, mode: str) -> GuardResult:
        target = Path(path_str).resolve()
        if mode == "write":
            allowed = any(
                target == d
                or str(target).startswith(str(d) + "/")
                or str(target).startswith(str(d) + "\\")
                for d in self._writable_dirs
            )
            if not allowed:
                return GuardResult(action=GuardAction.BLOCK, layer=1, reason=f"Write outside sandbox: {target}")
        elif mode == "read":
            allowed = any(
                target == d
                or str(target).startswith(str(d) + "/")
                or str(target).startswith(str(d) + "\\")
                for d in self._readable_dirs
            )
            if not allowed:
                return GuardResult(action=GuardAction.BLOCK, layer=1, reason=f"Read outside sandbox: {target}")
        return GuardResult(action=GuardAction.ALLOW, layer=1)
