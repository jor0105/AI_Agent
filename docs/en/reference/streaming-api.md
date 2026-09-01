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

Returns string representation.

**Returns**: Full string if consumed, placeholder otherwise:
`StreamingResponseDTO(not consumed - use "await response")`

**Example**:

```python
print(str(dto))  # "StreamingResponseDTO(not consumed - use "await response")"
```

#### `__repr__() -> str`

Returns debugging representation with consumption status and character length.

______________________________________________________________________

## Usage Patterns

### Pattern 1: Direct Await for Complete String

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('Hello')  # Returns StreamingResponseDTO
    text = (
        await response
    )  # Consumes stream and returns complete string (cached)
    print(text)


asyncio.run(main())
```

### Pattern 2: `async for` Token Streaming

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('Tell a story')

    async for token in response:
        print(token, end='', flush=True)
    print()


asyncio.run(main())
```

### Pattern 3: Accumulate While Displaying

```python
import asyncio
from createagents import CreateAgent


async def accumulate_and_display():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('List 5 tips')

    accumulated = ''
    async for token in response:
        accumulated += token
        print(token, end='', flush=True)

    print(f'\n\nTotal characters: {len(accumulated)}')


asyncio.run(accumulate_and_display())
```

______________________________________________________________________

## Internal Properties

| Property         | Type                        | Description                                |
| ---------------- | --------------------------- | ------------------------------------------ |
| `_generator`     | `AsyncGenerator[str, None]` | Underlying token async generator           |
| `_consumed`      | `bool`                      | Flag indicating if the stream was consumed |
| `_full_response` | `str`                       | Concatenated string cached in memory       |

______________________________________________________________________

## Consumption Semantics and Iteration

### Consumption and Caching

- **Via `await response`**: Completely drains the asynchronous generator and stores concatenated text in `_full_response`. Subsequent `await response` calls immediately return the cached string.
- **Via `async for token in response:`**: Consumes tokens progressively until the generator is exhausted, setting `_consumed = True`.
- **Second `async for` loop**: Since the underlying generator is already exhausted, a second `async for` finishes immediately with 0 items (the `async for` constructs catch `StopAsyncIteration` internally and exit cleanly).
- **Direct `response.__anext__()` call**: If invoked directly on an already exhausted generator, explicitly raises `StopAsyncIteration`.

______________________________________________________________________

## Exceptions

### `StopAsyncIteration`

Raised when iteration finishes on the underlying token generator.

```python
async def demo_loop(response):
    async for token in response:
        print(token)
    # StopAsyncIteration is caught internally when the generator completes
```

______________________________________________________________________

## See Also

- [Streaming User Guide](../user-guide/streaming-guide.md)
- [Async Developer Guide](../dev-guide/async-guide.md)
- [API Reference](api.md)

______________________________________________________________________

**Version:** 0.3.0 | **Updated:** 2026-08-27
