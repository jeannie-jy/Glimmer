"""Tests for tool registry."""
import pytest
from harness.tools.registry import ToolRegistry, Tool
from harness.models import ToolCall, ToolResult


class _EchoTool(Tool):
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "Echo back input"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(tool_name="echo", exit_code=0, stdout=arguments.get("text", ""))


class TestToolRegistry:
    def test_register_and_list_tools(self):
        registry = ToolRegistry()
        registry.register(_EchoTool())

        defs = registry.list_defs()
        assert len(defs) == 1
        assert defs[0].name == "echo"

    async def test_dispatch_calls_correct_tool(self):
        registry = ToolRegistry()
        registry.register(_EchoTool())

        result = await registry.dispatch(ToolCall(id="1", name="echo", arguments={"text": "hello"}))

        assert result.exit_code == 0
        assert result.stdout == "hello"

    async def test_dispatch_unknown_tool_raises(self):
        registry = ToolRegistry()

        with pytest.raises(ValueError, match="Unknown tool"):
            await registry.dispatch(ToolCall(id="1", name="nonexistent", arguments={}))

    def test_duplicate_registration_raises(self):
        registry = ToolRegistry()
        registry.register(_EchoTool())

        with pytest.raises(ValueError, match="already registered"):
            registry.register(_EchoTool())
