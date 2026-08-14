"""Unit tests for LLM adapter message conversion.

Regression tests for the tool_use round-trip bug: assistant messages with
tool calls were persisted without their tool_calls, so re-sending the
conversation to a real provider produced unpaired tool_result blocks and a
400 on every multi-turn tool conversation (worse after guardrail
BLOCK/REJECT, which dropped the tool message entirely).
"""
import json

from harness.llm.anthropic import AnthropicAdapter
from harness.llm.openai import OpenAIAdapter
from harness.models import Message, ToolCall


def _assistant_with_tools(content: str = "") -> Message:
    return Message(
        role="assistant",
        content=content,
        tool_calls=[ToolCall(id="t1", name="read_file", arguments={"path": "a.py"})],
    )


class TestAnthropicConversion:
    def test_assistant_tool_use_roundtrip(self):
        msgs = [
            _assistant_with_tools(""),
            Message(role="tool", content="Exit code: 0\nok", tool_call_id="t1"),
        ]
        converted = AnthropicAdapter._to_anthropic_messages(msgs)

        assistant_blocks = converted[0]["content"]
        assert any(
            b.get("type") == "tool_use"
            and b["id"] == "t1"
            and b["name"] == "read_file"
            and b["input"] == {"path": "a.py"}
            for b in assistant_blocks
        ), f"assistant tool_use block missing: {assistant_blocks}"

        assert converted[1]["role"] == "user"
        tool_result = converted[1]["content"][0]
        assert tool_result["type"] == "tool_result"
        assert tool_result["tool_use_id"] == "t1"

    def test_empty_content_produces_no_empty_text_block(self):
        converted = AnthropicAdapter._to_anthropic_messages([_assistant_with_tools("")])
        assert converted[0]["content"], "content blocks must not be empty"
        assert all(
            b.get("type") != "text" or b["text"] != "" for b in converted[0]["content"]
        )

    def test_text_and_tool_use_both_preserved(self):
        converted = AnthropicAdapter._to_anthropic_messages(
            [_assistant_with_tools("Let me check the file.")]
        )
        blocks = converted[0]["content"]
        assert any(b.get("type") == "text" and b["text"] == "Let me check the file." for b in blocks)
        assert any(b.get("type") == "tool_use" for b in blocks)


class TestOpenAIConversion:
    def test_assistant_tool_calls_roundtrip(self):
        msgs = [
            _assistant_with_tools("Let me check."),
            Message(role="tool", content="Exit code: 0", tool_call_id="t1"),
        ]
        converted = OpenAIAdapter._to_openai_messages(msgs)

        assert converted[0]["role"] == "assistant"
        assert converted[0]["tool_calls"] == [{
            "id": "t1",
            "type": "function",
            "function": {"name": "read_file", "arguments": json.dumps({"path": "a.py"})},
        }]
        assert converted[1] == {
            "role": "tool",
            "tool_call_id": "t1",
            "content": "Exit code: 0",
        }

    def test_assistant_without_tools_has_no_tool_calls_key(self):
        converted = OpenAIAdapter._to_openai_messages(
            [Message(role="assistant", content="plain text")]
        )
        assert "tool_calls" not in converted[0]
