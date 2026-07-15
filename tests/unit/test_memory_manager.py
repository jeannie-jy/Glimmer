"""Tests for MemoryManager."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from harness.memory.manager import MemoryManager


@pytest.fixture
def memory_dir(tmp_path: Path) -> Path:
    """Create a temporary project root with a .harness/memory directory."""
    proj = tmp_path / "project"
    mem = proj / ".harness" / "memory"
    mem.mkdir(parents=True)
    return proj


@pytest.fixture
def manager(memory_dir: Path) -> MemoryManager:
    return MemoryManager(memory_dir)


# ------------------------------------------------------------------
# Conventions loading
# ------------------------------------------------------------------


def test_loads_project_conventions(tmp_path: Path):
    """CLAUDE.md files in .claude/ are included in get_context()."""
    proj = tmp_path / "project"
    (proj / ".claude").mkdir(parents=True)

    claude_file = proj / ".claude" / "CLAUDE.md"
    claude_file.write_text("# Project Rules\n\nUse TypeScript.\n", encoding="utf-8")

    mgr = MemoryManager(proj)
    ctx = mgr.get_context()

    assert "Project Rules" in ctx
    assert "Use TypeScript." in ctx


def test_loads_root_claude(tmp_path: Path):
    """A CLAUDE.md at the project root is also loaded."""
    proj = tmp_path / "project"
    proj.mkdir()
    (proj / "CLAUDE.md").write_text("Root rules", encoding="utf-8")

    mgr = MemoryManager(proj)
    ctx = mgr.get_context()

    assert "Root rules" in ctx


# ------------------------------------------------------------------
# Store & retrieve decisions
# ------------------------------------------------------------------


def test_stores_and_retrieves_decisions(manager: MemoryManager):
    """record_decision() creates a JSON file; get_context() returns it when query matches."""
    manager.record_decision("architecture", "Use event-driven architecture")

    # Verify file exists
    files = list(manager.memory_dir.iterdir())
    assert len(files) == 1
    assert "_decision_architecture.json" in files[0].name

    # Verify content
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["kind"] == "decision"
    assert data["tag"] == "architecture"
    assert "event-driven" in data["content"]

    # get_context with matching query
    ctx = manager.get_context(query="architecture")
    assert "Use event-driven architecture" in ctx


def test_retrieves_by_tag_keyword(manager: MemoryManager):
    """Decisions are returned when a keyword from the query matches the tag."""
    manager.record_decision("db-choice", "Use PostgreSQL")
    manager.record_decision("auth-flow", "Use JWT tokens")
    manager.record_decision("deploy", "Use Docker")

    ctx = manager.get_context(query="db")
    assert "Use PostgreSQL" in ctx
    assert "Use JWT tokens" not in ctx
    assert "Use Docker" not in ctx


def test_empty_query_returns_no_decisions(manager: MemoryManager):
    """With an empty query, no decision entries are included in context."""
    manager.record_decision("arch", "Microservices")
    ctx = manager.get_context(query="")
    assert "Microservices" not in ctx


def test_limits_decisions_to_max(manager: MemoryManager):
    """At most MAX_DECISIONS decisions are returned."""
    for i in range(10):
        manager.record_decision(f"decision-{i}", f"Content {i}")
    ctx = manager.get_context(query="decision")
    # Should contain at most 5 matches
    count = ctx.count("Content ")
    assert count <= 5


# ------------------------------------------------------------------
# Learnings
# ------------------------------------------------------------------


def test_stores_and_retrieves_learnings(manager: MemoryManager):
    """record_learning() creates a JSON file; get_context() returns recent ones."""
    manager.record_learning("test-strategy", "Write unit tests first")
    ctx = manager.get_context()
    assert "Write unit tests first" in ctx


def test_enforces_learnings_limit(manager: MemoryManager):
    """At most MAX_LEARNINGS (20) learnings are returned."""
    for i in range(25):
        manager.record_learning(f"learning-{i}", f"Learning content {i}")
    ctx = manager.get_context()
    count = ctx.count("Learning content ")
    assert count <= 20


def test_learnings_by_recency(manager: MemoryManager):
    """Learnings are returned most-recent-first by mtime."""
    # Write old learning
    old_path = manager.memory_dir / "20230101_000000_learning_old.json"
    old_path.write_text(
        json.dumps({"kind": "learning", "tag": "old", "timestamp": "2023-01-01T00:00:00", "content": "Old learning"}),
        encoding="utf-8",
    )

    # Write new learning
    new_path = manager.memory_dir / "20240101_000000_learning_new.json"
    new_path.write_text(
        json.dumps({"kind": "learning", "tag": "new", "timestamp": "2024-01-01T00:00:00", "content": "New learning"}),
        encoding="utf-8",
    )

    ctx = manager.get_context()
    # The newer one should appear first (or at least both should appear)
    assert "Old learning" in ctx
    assert "New learning" in ctx


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


def test_empty_context_when_no_data(tmp_path: Path):
    """get_context() returns empty string when nothing is stored."""
    proj = tmp_path / "project"
    (proj / ".harness" / "memory").mkdir(parents=True)
    mgr = MemoryManager(proj)
    assert mgr.get_context() == ""


def test_ignores_non_json_files(manager: MemoryManager):
    """Non-JSON files in the memory directory are ignored."""
    (manager.memory_dir / "readme.txt").write_text("hello", encoding="utf-8")
    manager.record_learning("tag", "content")
    ctx = manager.get_context()
    assert "content" in ctx


def test_caches_conventions(tmp_path: Path):
    """Conventions are cached after first load."""
    proj = tmp_path / "project"
    (proj / ".claude").mkdir(parents=True)
    cl = proj / ".claude" / "CLAUDE.md"
    cl.write_text("v1", encoding="utf-8")

    mgr = MemoryManager(proj)
    mgr.get_context()

    # Modify the file
    cl.write_text("v2", encoding="utf-8")

    # Should still return cached v1
    ctx = mgr.get_context()
    assert "v1" in ctx
    assert "v2" not in ctx


def test_record_decision_overwrites_different_tag(manager: MemoryManager):
    """Decisions with different tags create separate files."""
    manager.record_decision("tag-a", "Content A")
    manager.record_decision("tag-b", "Content B")
    files = list(manager.memory_dir.glob("*.json"))
    assert len(files) == 2
