"""File operation tools."""
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


class ReadFileTool(Tool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
                "offset": {"type": "integer", "description": "Line number to start reading from"},
                "limit": {"type": "integer", "description": "Maximum number of lines to read"},
            },
            "required": ["path"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        import time
        start = time.time()
        path = Path(arguments["path"])
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            offset = arguments.get("offset", 0)
            limit = arguments.get("limit")
            if offset > 0:
                lines = lines[offset - 1:]
            if limit is not None:
                lines = lines[:limit]
            result = "\n".join(lines)
            return ToolResult(
                tool_name="read_file",
                exit_code=0,
                stdout=result,
                duration_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                tool_name="read_file",
                exit_code=1,
                stderr=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )


class WriteFileTool(Tool):
    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Create or overwrite a file with new content."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to write"},
                "content": {"type": "string", "description": "Content to write to the file"},
            },
            "required": ["path", "content"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        import time
        start = time.time()
        path = Path(arguments["path"])
        content = arguments["content"]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ToolResult(
                tool_name="write_file",
                exit_code=0,
                stdout=f"Wrote {len(content)} bytes to {path}",
                duration_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                tool_name="write_file",
                exit_code=1,
                stderr=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )
