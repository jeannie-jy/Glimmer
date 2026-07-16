"""Shared data models for the harness."""

from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, PrivateAttr


class State(str, Enum):
    """Agent state machine states."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    CORRECTING = "correcting"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    ERROR = "error"


class Verdict(str, Enum):
    """Feedback analysis verdict."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


class GuardAction(str, Enum):
    """Guardrail check result action."""
    ALLOW = "allow"
    BLOCK = "block"
    ASK_HUMAN = "ask_human"


class TokenUsage(BaseModel):
    """LLM token usage counters."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ToolDef(BaseModel):
    """Tool definition for LLM function calling."""
    name: str
    description: str
    parameters: dict  # JSON Schema for the tool's parameters


class ToolCall(BaseModel):
    """A single tool invocation request."""
    id: str
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result of executing a tool."""
    tool_name: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    structured: dict | None = None


class Failure(BaseModel):
    """A single test/check failure."""
    file: str
    line: int | None = None
    function: str | None = None
    message: str = ""


class Feedback(BaseModel):
    """Structured feedback from analyzing tool results."""
    verdict: Verdict
    failures: list[Failure] = Field(default_factory=list)
    summary: str = ""
    suggested_fix: str = ""
    retry_count: int = 0


class GuardResult(BaseModel):
    """Result of a guardrail check."""
    action: GuardAction
    layer: int  # 1, 2, or 3
    reason: str = ""


class LLMResponse(BaseModel):
    """Unified LLM response across providers."""
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    stop_reason: str = ""  # "complete", "tool_use", "max_tokens", "error"
    usage: TokenUsage = Field(default_factory=TokenUsage)


class Message(BaseModel):
    """A single message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str = ""
    tool_call_id: str | None = None
    tool_result: ToolResult | None = None


class Session(BaseModel):
    """A complete agent task session."""
    id: str
    task: str
    state: State = State.IDLE
    messages: list[Message] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    retry_count: int = 0
    total_tokens: TokenUsage = Field(default_factory=TokenUsage)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Runtime-only state (not serialized) for human-in-the-loop
    _pending_approval: ToolCall | None = PrivateAttr(default=None)
    _guard_reason: str = PrivateAttr(default="")


class ConfigData(BaseModel):
    """Harness configuration."""
    model_provider: str = "anthropic"
    model_id: str = "claude-sonnet-5"
    base_url: str = ""
    max_tokens: int = 4096
    max_retries: int = 3
    sandbox_root: str = "."
    command_whitelist_extra: list[str] = Field(default_factory=list)
    timeout_seconds: int = 30
    enabled_tools: list[str] = Field(default_factory=lambda: [
        "read_file", "write_file", "execute_shell", "run_tests", "search_code"
    ])
    max_context_tokens: int = 8000
    learnings_limit: int = 20
