# Streaming API Reference

Complete technical reference for the streaming API of CreateAgents AI.

______________________________________________________________________

## `StreamingResponseDTO`

**Namespace**: `createagents.application.dtos`

Class encapsulating an `AsyncGenerator` to provide convenient consumption of streaming responses via async iteration or direct `await`.

### Signature

```python
class StreamingResponseDTO:
    def __init__(self, generator: AsyncGenerator[str, None]): ...

    async def __anext__(self) -> str: ...
    def __aiter__(self) -> 'StreamingResponseDTO': ...
    def __await__(self) -> Generator[Any, None, str]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
```

### Methods

#### `__init__(generator: AsyncGenerator[str, None])`

Initializes the DTO with an async generator yielding string tokens.

#### `__aiter__() -> StreamingResponseDTO`

Returns the iterator for `async for` loops.

#### `async __anext__() -> str`

Returns the next token from the stream. Raises `StopAsyncIteration` when exhausted.

#### `__await__() -> Generator`

Awaits and consumes the entire stream, returning the complete aggregated string.

#### `__str__() -> str`

Returns the accumulated string if consumed, or an unconsumed placeholder string.

______________________________________________________________________

## Usage Patterns

### Pattern 1: Direct Await for Complete String

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )
    response = await agent.chat('Hello')
    text = await response  # Full text
    print(text)


asyncio.run(main())
```

### Pattern 2: `async for` Token Streaming

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )
    response = await agent.chat('Tell a story')

    async for token in response:
        print(token, end='', flush=True)
    print()


asyncio.run(main())
```

______________________________________________________________________

## See Also

- [Streaming User Guide](../user-guide/streaming-guide.md)
- [Async Developer Guide](../dev-guide/async-guide.md)
- [API Reference](api.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
