from collections.abc import AsyncGenerator, Generator


class StreamingResponseDTO:
    """Data Transfer Object for streaming chat responses.

    Wraps an async generator to provide a clean interface for async iteration.
    Can be awaited to get the complete response string automatically.
    """

    def __init__(self, generator: AsyncGenerator[str, None]) -> None:
        """Initialize with a token generator.

        Args:
            generator: AsyncGenerator that yields response tokens as strings.

        """
        self._generator = generator
        self._consumed = False
        self._full_response = ''

    def __aiter__(self) -> 'StreamingResponseDTO':
        """Allow async iteration over tokens."""
        return self

    async def __anext__(self) -> str:
        """Get next token asynchronously."""
        if self._consumed:
            raise StopAsyncIteration

        try:
            token = await self._generator.__anext__()
        except StopAsyncIteration:
            self._consumed = True
            raise
        self._full_response += token
        return token

    def __await__(self) -> Generator[object, None, str]:
        """Allow awaiting to get complete response string.

        This method enables transparent usage:
            response = await agent.chat("message")  # StreamingResponseDTO
            text = await response  # Auto-consumes and returns complete string

        The CLI can still use async for without awaiting again.
        """

        async def _consume() -> str:
            """Consume all tokens and return complete response."""
            if self._consumed:
                return self._full_response

            # Tokens are accumulated in _full_response by __anext__
            async for _ in self:
                pass

            return self._full_response

        return _consume().__await__()

    def __str__(self) -> str:
        """Return string representation.

        Returns the full response if consumed, otherwise a placeholder.
        For unconsumed streams, await the response first to get the text.
        """
        if self._consumed:
            return self._full_response
        return 'StreamingResponseDTO(not consumed - use "await response")'

    def __repr__(self) -> str:
        """Return representation."""
        if self._consumed:
            return (
                'StreamingResponseDTO('
                f'consumed, length={len(self._full_response)})'
            )
        return 'StreamingResponseDTO(active)'
