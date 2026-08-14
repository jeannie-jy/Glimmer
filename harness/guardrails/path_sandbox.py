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
        p = Path(path_str)
        # Relative paths are relative to the sandbox root, not the process
        # cwd — the file tools resolve them against the workspace root, so a
        # cwd-relative check would block every relative path whenever the
        # sandbox root differs from cwd (e.g. WORKSPACE_ROOT=/workspace).
        target = (self._root / p).resolve() if not p.is_absolute() else p.resolve()
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
        else:
            return GuardResult(action=GuardAction.BLOCK, layer=1, reason=f"Unknown access mode: {mode}")
        return GuardResult(action=GuardAction.ALLOW, layer=1)
