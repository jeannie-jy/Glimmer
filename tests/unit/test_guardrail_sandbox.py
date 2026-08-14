"""Tests for Layer 1 path sandbox."""
from pathlib import Path
import pytest
from harness.guardrails.path_sandbox import PathSandbox
from harness.models import GuardAction


class TestPathSandbox:
    @pytest.fixture
    def sandbox(self, tmp_path):
        return PathSandbox(root=tmp_path)

    def test_allows_read_inside_root(self, sandbox, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("x = 1")
        result = sandbox.validate(str(f), "read")
        assert result.action == GuardAction.ALLOW

    def test_allows_write_inside_root(self, sandbox, tmp_path):
        f = tmp_path / "new.py"
        result = sandbox.validate(str(f), "write")
        assert result.action == GuardAction.ALLOW

    def test_blocks_read_outside_root(self, sandbox):
        result = sandbox.validate("/etc/passwd", "read")
        assert result.action == GuardAction.BLOCK

    def test_blocks_write_outside_root(self, sandbox):
        result = sandbox.validate("/etc/malicious", "write")
        assert result.action == GuardAction.BLOCK

    def test_blocks_symlink_escape(self, sandbox, tmp_path):
        # Even if resolve() escapes root, block it
        result = sandbox.validate(str(tmp_path / ".." / ".." / "etc" / "passwd"), "read")
        assert result.action == GuardAction.BLOCK

    def test_allows_relative_path_resolved_against_root(self, sandbox, tmp_path):
        # Relative paths must resolve against the sandbox root, not the
        # process cwd — otherwise agents writing under a workspace root that
        # differs from cwd (e.g. WORKSPACE_ROOT=/workspace on Render) get
        # every relative path blocked as "outside sandbox".
        f = tmp_path / "notes" / "a.txt"
        f.parent.mkdir()
        f.write_text("hi")
        result = sandbox.validate("notes/a.txt", "read")
        assert result.action == GuardAction.ALLOW

    def test_blocks_relative_traversal_escaping_root(self, sandbox):
        result = sandbox.validate("../outside.txt", "write")
        assert result.action == GuardAction.BLOCK
