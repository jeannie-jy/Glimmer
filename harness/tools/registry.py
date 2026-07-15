"""Tool registration and dispatch."""
from abc import ABC, abstractmethod
from harness.models import ToolDef, ToolCall, ToolResult


class Tool(ABC):
    """Interface for a tool the agent can invoke."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> dict: ...

    @abstractmethod
    async def execute(self, arguments: dict) -> ToolResult: ...

    def to_def(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, parameters=self.parameters)


class ToolRegistry:
    """Registry of available tools with dispatch."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def list_defs(self) -> list[ToolDef]:
        return [t.to_def() for t in self._tools.values()]

    async def dispatch(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            raise ValueError(f"Unknown tool: {call.name}")
        return await tool.execute(call.arguments)
