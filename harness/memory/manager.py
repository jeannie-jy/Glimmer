"""MemoryManager: stores and retrieves decisions and learnings as JSON files."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class MemoryManager:
    """Manages project memory as JSON files in .harness/memory/.

    Decisions and learnings are stored with {timestamp}_{tag}.json naming.
    get_context() loads project conventions and recent memory entries.
    """

    MEMORY_DIR = ".harness/memory"
    MAX_DECISIONS = 5
    MAX_LEARNINGS = 20

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.memory_dir = self.project_root / self.MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._conventions_cache: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_context(self, query: str = "") -> str:
        """Build a context string from conventions, matching decisions, and recent learnings."""
        parts: list[str] = []

        # 1. Project conventions (loaded once)
        conventions = self._load_conventions()
        if conventions:
            parts.append("=== Project Conventions ===\n" + conventions)

        # 2. Decisions matching the query (by keyword in filename)
        decisions = self._search_decisions(query)
        if decisions:
            parts.append("=== Relevant Decisions ===\n" + "\n---\n".join(decisions))

        # 3. Recent learnings (by mtime, up to MAX_LEARNINGS)
        learnings = self._recent_learnings()
        if learnings:
            parts.append("=== Recent Learnings ===\n" + "\n---\n".join(learnings))

        return "\n\n".join(parts) if parts else ""

    def record_decision(self, tag: str, content: str) -> None:
        """Record a decision under *tag*. Overwrites an existing decision with the same tag."""
        self._write_memory_file("decision", tag, content)

    def record_learning(self, tag: str, content: str) -> None:
        """Record a learning under *tag*. Older learnings with the same tag are not removed
        (each call creates a new timestamped file)."""
        self._write_memory_file("learning", tag, content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_conventions(self) -> str:
        """Read CLAUDE.md / conventions files from the project root."""
        if self._conventions_cache is not None:
            return self._conventions_cache

        candidates: list[Path] = []
        # Look for CLAUDE.md in .claude/ directory
        claude_dir = self.project_root / ".claude"
        if claude_dir.is_dir():
            candidates.extend(sorted(claude_dir.rglob("CLAUDE.md")))

        # Also check project root
        root_claude = self.project_root / "CLAUDE.md"
        if root_claude.is_file():
            candidates.append(root_claude)

        snippets: list[str] = []
        for path in candidates:
            try:
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    rel = path.relative_to(self.project_root)
                    snippets.append(f"--- {rel} ---\n{text}")
            except (OSError, ValueError):
                continue

        self._conventions_cache = "\n\n".join(snippets)
        return self._conventions_cache

    def _search_decisions(self, query: str) -> list[str]:
        """Search decision files whose filename contains a keyword from the query.
        Returns at most MAX_DECISIONS entries sorted by mtime (most recent first).
        """
        if not query:
            return []

        keywords = query.lower().split()
        matched: list[tuple[float, str]] = []

        for fpath in self.memory_dir.iterdir():
            if not fpath.name.endswith(".json"):
                continue
            if "_decision_" not in fpath.stem:
                continue
            # Keyword matching on the tag portion (after the timestamp)
            tag_part = fpath.stem.split("_", 2)[-1] if "_" in fpath.stem else fpath.stem
            if any(kw in tag_part.lower() for kw in keywords):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    mtime = fpath.stat().st_mtime
                    matched.append((mtime, data.get("content", "")))
                except (OSError, json.JSONDecodeError):
                    continue

        matched.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in matched[: self.MAX_DECISIONS]]

    def _recent_learnings(self) -> list[str]:
        """Load most recent learnings by mtime, up to MAX_LEARNINGS."""
        entries: list[tuple[float, str]] = []

        for fpath in self.memory_dir.iterdir():
            if not fpath.name.endswith(".json"):
                continue
            if "_learning_" not in fpath.stem:
                continue
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                mtime = fpath.stat().st_mtime
                entries.append((mtime, data.get("content", "")))
            except (OSError, json.JSONDecodeError):
                continue

        entries.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in entries[: self.MAX_LEARNINGS]]

    def _write_memory_file(self, kind: str, tag: str, content: str) -> None:
        """Write a JSON memory file: {timestamp}_{kind}_{tag}.json"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_tag = tag.replace(" ", "_").replace("/", "_")
        filename = f"{timestamp}_{kind}_{safe_tag}.json"
        fpath = self.memory_dir / filename

        data = {
            "kind": kind,
            "tag": tag,
            "timestamp": datetime.now().isoformat(),
            "content": content,
        }
        fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
