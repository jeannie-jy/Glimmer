"""OpenAI Chat Completions API adapter."""
from typing import AsyncIterator
from openai import AsyncOpenAI
from harness.llm.adapter import LLMAdapter
from harness.models import Message, ToolDef, LLMResponse, TokenUsage, ToolCall


class OpenAIAdapter(LLMAdapter):
    """Adapter for OpenAI's Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        kwargs = {"api_key": api_key, "timeout": 60.0}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = model

    @staticmethod
    def _to_openai_messages(messages: list[Message]) -> list[dict]:
        converted = []
        for m in messages:
            if m.role == "tool":
                converted.append({
                    "role": "tool",
                    "tool_call_id": m.tool_call_id,
                    "content": m.content,
                })
            else:
                converted.append({"role": m.role, "content": m.content})
        return converted

    @staticmethod
    def _to_openai_tools(tools: list[ToolDef]) -> list[dict]:
        return [{
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
        } for t in tools]

    async def chat(
        self, messages: list[Message], tools: list[ToolDef], stream: bool = True
    ) -> LLMResponse:
        openai_messages = self._to_openai_messages(messages)
        openai_tools = self._to_openai_tools(tools) if tools else None

        kwargs = {
            "model": self._model,
            "messages": openai_messages,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        content = choice.message.content or ""
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                import json
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason="tool_use" if tool_calls else "complete",
            usage=TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
        )

    async def chat_stream(
        self, messages: list[Message], tools: list[ToolDef]
    ) -> AsyncIterator[str]:
        openai_messages = self._to_openai_messages(messages)
        openai_tools = self._to_openai_tools(tools) if tools else None

        kwargs = {
            "model": self._model,
            "messages": openai_messages,
            "stream": True,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
