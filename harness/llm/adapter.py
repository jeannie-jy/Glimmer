"""Abstract base class for LLM adapters."""
from abc import ABC, abstractmethod
from typing import AsyncIterator
from harness.models import Message, ToolDef, LLMResponse


class LLMAdapter(ABC):
    """Unified interface for LLM providers.

    Each provider (Anthropic, OpenAI, Mock) implements this interface.
    The harness core only depends on this ABC, never on concrete adapters.
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef],
        stream: bool = True,
    ) -> LLMResponse:
        """Send a conversation to the LLM and get a response.

        Args:
            messages: Conversation history.
            tools: Available tool definitions for function calling.
            stream: If True, stream tokens; if False, return complete response.

        Returns:
            Unified LLMResponse with content and/or tool_calls.
        """
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDef],
    ) -> AsyncIterator[str]:
        """Stream text tokens from the LLM.

        Args:
            messages: Conversation history.
            tools: Available tool definitions.

        Yields:
            Text chunks (individual tokens or small groups).
        """
        ...
