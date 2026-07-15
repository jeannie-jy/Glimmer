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
