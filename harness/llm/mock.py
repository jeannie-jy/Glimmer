"""Mock LLM adapter for deterministic testing."""
from typing import AsyncIterator
from harness.llm.adapter import LLMAdapter
from harness.models import Message, ToolDef, LLMResponse


class MockLLMAdapter(LLMAdapter):
    """LLM adapter that returns pre-programmed responses.

    Used in unit tests to deterministically verify harness behavior
    without real LLM calls. Responses are consumed in FIFO order.
    """

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self._index = 0
        self.call_history: list[dict] = []

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef],
        stream: bool = True,
    ) -> LLMResponse:
        self.call_history.append({"messages": messages, "tools": tools})
        if self._index >= len(self._responses):
            raise IndexError(
                f"No more mock responses (called {self._index + 1} times, "
                f"only {len(self._responses)} responses programmed)"
            )
        response = self._responses[self._index]
        self._index += 1
        return response

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDef],
    ) -> AsyncIterator[str]:
        response = await self.chat(messages, tools)
        # Simulate streaming by yielding content in word-based chunks
        words = response.content.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
