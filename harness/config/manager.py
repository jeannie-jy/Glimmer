"""ConfigManager: loads and merges project / global YAML configs into ConfigData."""

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from harness.models import ConfigData

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge *override* into *base* and return a new dict.

    - Scalars in *override* overwrite *base*.
    - Lists in *override* are *appended* to *base* lists (the brief says "lists appended").
    - Nested dicts are merged recursively.
    """
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        elif key in result and isinstance(result[key], list) and isinstance(val, list):
            result[key] = result[key] + val
        else:
            result[key] = deepcopy(val)
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning an empty dict if it doesn't exist or YAML is unavailable."""
    if yaml is None:
        return {}
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}
        return data
    except Exception:
        return {}


def _normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested YAML groups into the top-level ConfigData fields.

    The project config.yaml uses nested groups like:
        model:
          provider: anthropic
          model_id: claude-sonnet-5
        guardrails:
          max_retries: 3
        tools:
          enabled: [read_file, ...]
        memory:
          max_context_tokens: 8000

    ConfigData expects flat keys like:
        model_provider, model_id, max_retries, enabled_tools, max_context_tokens, ...
    """
    flat: dict[str, Any] = {}

    if "model" in raw:
        m = raw["model"]
        if isinstance(m, dict):
            if "provider" in m:
                flat["model_provider"] = m["provider"]
            if "model_id" in m:
                flat["model_id"] = m["model_id"]
            if "max_tokens" in m:
                flat["max_tokens"] = m["max_tokens"]

    if "guardrails" in raw:
        g = raw["guardrails"]
        if isinstance(g, dict):
            if "max_retries" in g:
                flat["max_retries"] = g["max_retries"]
            if "sandbox_root" in g:
                flat["sandbox_root"] = g["sandbox_root"]
            if "command_whitelist_extra" in g:
                flat["command_whitelist_extra"] = g["command_whitelist_extra"]
            if "timeout_seconds" in g:
                flat["timeout_seconds"] = g["timeout_seconds"]

    if "tools" in raw:
        t = raw["tools"]
        if isinstance(t, dict) and "enabled" in t:
            flat["enabled_tools"] = t["enabled"]

    if "memory" in raw:
        mem = raw["memory"]
        if isinstance(mem, dict):
            if "max_context_tokens" in mem:
                flat["max_context_tokens"] = mem["max_context_tokens"]
            if "learnings_limit" in mem:
                flat["learnings_limit"] = mem["learnings_limit"]

    return flat


class ConfigManager:
    """Loads and merges project + global YAML configs.

    Priority (highest to lowest): project config > global config > built-in defaults.
    Lists from higher-priority sources are *appended* to lower-priority lists.
    """

    PROJECT_CONFIG_PATH = ".harness/config.yaml"
    GLOBAL_CONFIG_PATH = "~/.harness/config.yaml"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()
        self._project_path = self.project_root / self.PROJECT_CONFIG_PATH
        self._global_path = Path(self.GLOBAL_CONFIG_PATH).expanduser()

    def load(self) -> ConfigData:
        """Load, merge, and return a ConfigData instance.

        Merge order:
          1. Start with ConfigData() defaults (flattened to dict).
          2. Deep-merge global config on top.
          3. Deep-merge project config on top.
          4. Normalise nested groups to flat keys.
          5. Construct ConfigData from the final dict.
        """
        # 1. Built-in defaults as a dict
        defaults = ConfigData().model_dump()

        # 2. Global config
        global_raw = _load_yaml(self._global_path)
        global_flat = _normalize_config(global_raw)
        merged = _deep_merge(defaults, global_flat)

        # 3. Project config
        project_raw = _load_yaml(self._project_path)
        project_flat = _normalize_config(project_raw)
        merged = _deep_merge(merged, project_flat)

        # 4. Construct and return
        return ConfigData(**merged)
