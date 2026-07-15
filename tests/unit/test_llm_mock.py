"""Tests for MockLLM adapter."""
import pytest
from harness.llm.adapter import LLMAdapter
from harness.llm.mock import MockLLMAdapter
from harness.models import Message, ToolDef, LLMResponse


class TestMockLLMAdapter:
    async def test_returns_preprogrammed_responses_in_sequence(self):
        """MockLLM should return responses in the order they were programmed."""
        responses = [
            LLMResponse(content="I'll look at the code first.", stop_reason="complete"),
            LLMResponse(content="", stop_reason="tool_use", tool_calls=[
                {"id": "call_1", "name": "read_file", "arguments": {"path": "test.py"}}
            ]),
            LLMResponse(content="The bug is fixed.", stop_reason="complete"),
        ]
        adapter = MockLLMAdapter(responses)

        r1 = await adapter.chat([Message(role="user", content="Fix the bug")], [])
        assert r1.content == "I'll look at the code first."
        assert r1.stop_reason == "complete"

        r2 = await adapter.chat([Message(role="user", content="Continue")], [])
        assert r2.stop_reason == "tool_use"
        assert len(r2.tool_calls) == 1
        assert r2.tool_calls[0].name == "read_file"

        r3 = await adapter.chat([Message(role="user", content="Continue")], [])
        assert r3.content == "The bug is fixed."

    async def test_raises_when_no_more_responses(self):
        """MockLLM should raise when called more times than programmed responses."""
        adapter = MockLLMAdapter([LLMResponse(content="Done.", stop_reason="complete")])

        await adapter.chat([Message(role="user", content="Task 1")], [])

        with pytest.raises(IndexError, match="No more mock responses"):
            await adapter.chat([Message(role="user", content="Task 2")], [])

    async def test_records_call_history(self):
        """MockLLM should record all calls for inspection in tests."""
        adapter = MockLLMAdapter([
            LLMResponse(content="First"),
            LLMResponse(content="Second"),
        ])

        await adapter.chat([Message(role="user", content="Q1")], [])
        await adapter.chat([Message(role="user", content="Q2")], [])

        assert len(adapter.call_history) == 2
        assert adapter.call_history[0]["messages"][0].content == "Q1"
        assert adapter.call_history[1]["messages"][0].content == "Q2"

    async def test_stream_yields_content_in_chunks(self):
        """MockLLM streaming should yield content in simulated chunks."""
        adapter = MockLLMAdapter([
            LLMResponse(content="Hello world"),
        ])

        chunks = []
        async for chunk in adapter.chat_stream(
            [Message(role="user", content="Hi")], []
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "".join(chunks) == "Hello world"
