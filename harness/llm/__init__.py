"""LLM abstraction layer."""
from harness.llm.adapter import LLMAdapter
from harness.llm.mock import MockLLMAdapter

__all__ = ["LLMAdapter", "MockLLMAdapter"]
