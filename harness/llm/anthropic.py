"""Anthropic Messages API adapter."""
from typing import AsyncIterator
import anthropic
from harness.llm.adapter import LLMAdapter
from harness.models import Message, ToolDef, LLMResponse, TokenUsage, ToolCall


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic's Messages API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-5-20251001"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=60.0)
        self._model = model

    @staticmethod
    def _to_anthropic_messages(messages: list[Message]) -> list[dict]:
        converted = []
        for m in messages:
            if m.role == "system":
                continue  # handled separately
            if m.role == "tool":
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_call_id,
                        "content": m.content,
                    }]
                })
            else:
                converted.append({"role": m.role, "content": m.content})
        return converted

    @staticmethod
    def _to_anthropic_tools(tools: list[ToolDef]) -> list[dict]:
        return [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools]

    async def chat(
        self, messages: list[Message], tools: list[ToolDef], stream: bool = True
    ) -> LLMResponse:
        system_msg = next((m.content for m in messages if m.role == "system"), "")
        anthropic_messages = self._to_anthropic_messages(messages)
        anthropic_tools = self._to_anthropic_tools(tools) if tools else None

        kwargs = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = await self._client.messages.create(**kwargs)

        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason="tool_use" if tool_calls else "complete",
            usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
        )

    async def chat_stream(
        self, messages: list[Message], tools: list[ToolDef]
    ) -> AsyncIterator[str]:
        system_msg = next((m.content for m in messages if m.role == "system"), "")
        anthropic_messages = self._to_anthropic_messages(messages)
        anthropic_tools = self._to_anthropic_tools(tools) if tools else None

        kwargs = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
