"""Tests for ConfigManager merge logic."""

from pathlib import Path
from harness.config.manager import ConfigManager, _deep_merge, _normalize_config
from harness.models import ConfigData


# ------------------------------------------------------------------
# Unit: _deep_merge helper
# ------------------------------------------------------------------


def test_deep_merge_scalar_overwrites():
    base = {"a": 1, "b": 2}
    override = {"b": 99}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": 99}


def test_deep_merge_lists_appended():
    base = {"items": [1, 2]}
    override = {"items": [3, 4]}
    result = _deep_merge(base, override)
    assert result == {"items": [1, 2, 3, 4]}


def test_deep_merge_nested_dicts():
    base = {"db": {"host": "localhost", "port": 5432}}
    override = {"db": {"port": 9999}}
    result = _deep_merge(base, override)
    assert result == {"db": {"host": "localhost", "port": 9999}}


def test_deep_merge_new_key_added():
    base = {"a": 1}
    override = {"b": 2}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": 2}


def test_deep_merge_empty_override():
    base = {"a": 1}
    result = _deep_merge(base, {})
    assert result == {"a": 1}


def test_deep_merge_empty_base():
    result = _deep_merge({}, {"a": 1})
    assert result == {"a": 1}


# ------------------------------------------------------------------
# Unit: _normalize_config
# ------------------------------------------------------------------


def test_normalize_config_standard():
    raw = {
        "model": {"provider": "anthropic", "model_id": "claude-sonnet-5", "max_tokens": 8192},
        "guardrails": {"max_retries": 5, "sandbox_root": "/tmp/sandbox", "timeout_seconds": 60},
        "tools": {"enabled": ["read_file", "write_file"]},
        "memory": {"max_context_tokens": 16000, "learnings_limit": 50},
    }
    flat = _normalize_config(raw)
    assert flat["model_provider"] == "anthropic"
    assert flat["model_id"] == "claude-sonnet-5"
    assert flat["max_tokens"] == 8192
    assert flat["max_retries"] == 5
    assert flat["sandbox_root"] == "/tmp/sandbox"
    assert flat["timeout_seconds"] == 60
    assert flat["enabled_tools"] == ["read_file", "write_file"]
    assert flat["max_context_tokens"] == 16000
    assert flat["learnings_limit"] == 50


def test_normalize_empty():
    assert _normalize_config({}) == {}


def test_normalize_partial():
    raw = {"model": {"provider": "openai"}}
    flat = _normalize_config(raw)
    assert flat["model_provider"] == "openai"
    # Other fields should not be set
    assert "model_id" not in flat
    assert "max_retries" not in flat


# ------------------------------------------------------------------
# Integration: ConfigManager.load
# ------------------------------------------------------------------


def test_defaults_when_no_config(tmp_path: Path):
    """When neither project nor global config exists, built-in defaults are used."""
    proj = tmp_path / "project"
    (proj / ".harness" / "memory").mkdir(parents=True)
    mgr = ConfigManager(proj)
    cfg = mgr.load()
    assert isinstance(cfg, ConfigData)
    assert cfg.model_provider == "anthropic"
    assert cfg.model_id == "claude-sonnet-5"
    assert cfg.max_tokens == 4096
    assert cfg.max_retries == 3
    assert cfg.enabled_tools == ["read_file", "write_file", "execute_shell", "run_tests", "search_code"]
    assert cfg.learnings_limit == 20
    assert cfg.max_context_tokens == 8000


def test_project_overrides_global(tmp_path: Path):
    """Project config values take precedence over global config."""
    proj = tmp_path / "project"
    (proj / ".harness").mkdir(parents=True)

    # Global config
    global_dir = tmp_path / "global_home"
    (global_dir / ".harness").mkdir(parents=True)
    global_cfg = global_dir / ".harness" / "config.yaml"
    global_cfg.write_text(
        "model:\n  provider: openai\n  model_id: gpt-4\n  max_tokens: 2048\n",
        encoding="utf-8",
    )

    # Project config (should override provider but keep model_id)
    proj_cfg = proj / ".harness" / "config.yaml"
    proj_cfg.write_text(
        "model:\n  provider: anthropic\n  max_tokens: 4096\n",
        encoding="utf-8",
    )

    mgr = ConfigManager(proj)
    # Replace global path resolution for testing
    mgr._global_path = global_dir / ".harness" / "config.yaml"

    cfg = mgr.load()
    assert cfg.model_provider == "anthropic"  # from project
    assert cfg.model_id == "gpt-4"  # from global (not overridden)
    assert cfg.max_tokens == 4096  # from project


def test_lists_are_appended(tmp_path: Path):
    """command_whitelist_extra / enabled_tools lists append rather than overwrite."""
    proj = tmp_path / "project"
    (proj / ".harness").mkdir(parents=True)

    # Global config
    global_dir = tmp_path / "global_home"
    (global_dir / ".harness").mkdir(parents=True)
    global_cfg = global_dir / ".harness" / "config.yaml"
    global_cfg.write_text(
        "tools:\n  enabled: [read_file, write_file]\n",
        encoding="utf-8",
    )

    # Project config appends more tools
    proj_cfg = proj / ".harness" / "config.yaml"
    proj_cfg.write_text(
        "tools:\n  enabled: [execute_shell, search_code]\n",
        encoding="utf-8",
    )

    mgr = ConfigManager(proj)
    mgr._global_path = global_dir / ".harness" / "config.yaml"

    cfg = mgr.load()
    # Merge order: defaults (5 tools), + global (appends 2), + project (appends 2) = 9.
    assert len(cfg.enabled_tools) == 9
    assert cfg.enabled_tools.count("read_file") == 2
    assert cfg.enabled_tools.count("write_file") == 2
    assert cfg.enabled_tools.count("execute_shell") == 2
    assert cfg.enabled_tools.count("search_code") == 2
    assert cfg.enabled_tools.count("run_tests") == 1  # only in defaults


def test_global_config_extends_defaults(tmp_path: Path):
    """Global config fills in fields that defaults already have -- global overrides scalar defaults."""
    proj = tmp_path / "project"
    (proj / ".harness").mkdir(parents=True)

    global_dir = tmp_path / "global_home"
    (global_dir / ".harness").mkdir(parents=True)
    global_cfg = global_dir / ".harness" / "config.yaml"
    global_cfg.write_text(
        "model:\n  provider: openai\n  max_tokens: 2048\n",
        encoding="utf-8",
    )

    mgr = ConfigManager(proj)
    mgr._global_path = global_dir / ".harness" / "config.yaml"

    cfg = mgr.load()
    assert cfg.model_provider == "openai"  # from global
    assert cfg.model_id == "claude-sonnet-5"  # from defaults
    assert cfg.max_tokens == 2048  # from global


def test_command_whitelist_append(tmp_path: Path):
    """command_whitelist_extra is appended across merge layers."""
    proj = tmp_path / "project"
    (proj / ".harness").mkdir(parents=True)

    global_dir = tmp_path / "global_home"
    (global_dir / ".harness").mkdir(parents=True)
    global_cfg = global_dir / ".harness" / "config.yaml"
    global_cfg.write_text(
        "guardrails:\n  command_whitelist_extra: [npm]\n",
        encoding="utf-8",
    )

    proj_cfg = proj / ".harness" / "config.yaml"
    proj_cfg.write_text(
        "guardrails:\n  command_whitelist_extra: [pip]\n",
        encoding="utf-8",
    )

    mgr = ConfigManager(proj)
    mgr._global_path = global_dir / ".harness" / "config.yaml"

    cfg = mgr.load()
    # Defaults: [], global adds [npm], project adds [pip]
    assert cfg.command_whitelist_extra == ["npm", "pip"]


def test_defaults_fill_gaps(tmp_path: Path):
    """When config only specifies a subset, defaults fill the rest."""
    proj = tmp_path / "project"
    (proj / ".harness").mkdir(parents=True)

    proj_cfg = proj / ".harness" / "config.yaml"
    proj_cfg.write_text(
        "model:\n  provider: openai\n",
        encoding="utf-8",
    )

    mgr = ConfigManager(proj)
    cfg = mgr.load()
    assert cfg.model_provider == "openai"
    # Everything else should be default
    assert cfg.model_id == "claude-sonnet-5"
    assert cfg.max_retries == 3
    assert cfg.sandbox_root == "."
    assert cfg.timeout_seconds == 30
