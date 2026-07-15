"""Lite Agent Harness -- A lightweight, model-agnostic coding agent harness with
deterministic guardrails, multi-provider LLM support, and mock-driven testing.

Sub-packages
------------
config      YAML config loading and merging (project global > defaults).
credentials Secure API key storage via OS keyring or AES-GCM encrypted files.
feedback    Deterministic feedback analysis with pytest JSON report parsing.
guardrails  Three-layer safety system: path sandbox, command whitelist, regex
            blacklist.
llm         Pluggable LLM adapters (Anthropic, OpenAI, Mock for testing).
memory      Decision and learning persistence as timestamped JSON files.
tools       Agent tool definitions and registry (file_ops, shell, code_search).

Key modules
-----------
loop            Main agent event loop coordinating all components.
models          Shared pydantic data models (Session, Message, ToolCall, ...).
state_machine   Deterministic state transition table -- pure function, no LLM.
"""
