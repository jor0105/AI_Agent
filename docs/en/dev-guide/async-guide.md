# Asynchronous Programming Guide

This guide explains how asynchronous programming and streaming operate in CreateAgents AI.

______________________________________________________________________

## 🔄 Why Async?

CreateAgents AI uses asynchronous programming for:

- **Real-Time Streaming**: Low-latency token delivery from OpenAI and Ollama APIs
- **Non-Blocking Tools**: Efficient execution of long-running tools
- **High Concurrency**: Processing multiple agent turns concurrently without thread blocking

______________________________________________________________________

## 🎯 Asynchronous Components

### `ChatRepository` (Interface)

```python
class ChatRepository(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        """Asynchronous chat returning a complete string or an AsyncGenerator."""
        pass

    @abstractmethod
    def get_metrics(self) -> list[ChatMetrics]:
        """Returns metrics collected across interactions."""
        pass
```

### `ChatAdapter` (Implementation)

```python
class OpenAIChatAdapter(ChatRepository):
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        if config and config.get('stream'):
            stream_handler = OpenAIStreamHandler(self.__client, self.__metrics)
            return stream_handler.handle_stream(
                model, instructions, messages, config, tools
            )

        handler = OpenAIHandler(self.__client, self.__metrics)
        return await handler.execute_tool_loop(
            model, instructions, messages, config, tools
        )
```

______________________________________________________________________

## 🛠️ Asynchronous Tool Execution

### `ToolExecutor`

```python
class ToolExecutor:
    def __init__(self, tools: list[BaseTool], logger: LoggerInterface) -> None:
        self._tools_map = {tool.name: tool for tool in tools}
        self.__logger = logger

    async def execute_tool(
        self, tool_name: str, **kwargs: Any
    ) -> ToolExecutionResult:
        self.__logger.info("Executing tool: '%s'", tool_name)

        try:
            tool = self._tools_map[tool_name]
            # Supports both async coroutines and sync functions in thread pool
            if asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**kwargs)
            else:
                result = await _wait_for_sync_result(
                    _TOOL_THREAD_POOL.submit(tool.execute, **kwargs)
                )

            return ToolExecutionResult(
                tool_name=tool_name, success=True, result=result
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name=tool_name, success=False, error=str(e)
            )
```

______________________________________________________________________

## 🔄 Complete Asynchronous Flows

### Without Tools

```
User: await agent.chat("message")
  → ChatWithAgentUseCase.execute() [async]
      → ChatRepository.chat() [async]
          → OpenAIStreamHandler.handle_stream() [async if stream=True]
              → async for chunk in openai_stream:
                  → yield chunk
          ← AsyncGenerator[str, None]
      ← StreamingResponseDTO
  ← await response (full string) or async for token in response
```

### With Tools

```
User: await agent.chat("What day is today?")
  → ChatWithAgentUseCase.execute() [async]
      → ChatRepository.chat() [async]
          → OpenAIStreamHandler / OpenAIHandler [async]
              → Detects tool_calls in API response
              → For each tool_call:
                  → ToolExecutor.execute_tool(tool_name, **args) [async]
                      ← ToolExecutionResult
              → Next iteration with tool results in message history
              → yield token (or returns final text)
          ← StreamingResponseDTO (if stream=True) or str (if stream=False)
  ← await response
```

______________________________________________________________________

## 💡 Usage Patterns

### Pattern 1: Direct Await

```python
import asyncio
from createagents import CreateAgent


async def simple_chat():
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    response = await agent.chat('Hello')
    print(response)


asyncio.run(simple_chat())
```

### Pattern 2: Token-by-Token Streaming

```python
import asyncio
from createagents import CreateAgent


async def streaming_chat():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('Tell me a story')

    async for token in response:
        print(token, end='', flush=True)
    print()


asyncio.run(streaming_chat())
```

### Pattern 3: Concurrent Execution with `asyncio.gather`

```python
import asyncio
from createagents import CreateAgent


async def concurrent_chats():
    agent1 = CreateAgent(provider='openai', model='YOUR_MODEL')
    agent2 = CreateAgent(provider='openai', model='YOUR_MODEL')

    results = await asyncio.gather(
        agent1.chat('Question 1'),
        agent2.chat('Question 2'),
    )

    print(results[0])
    print(results[1])


asyncio.run(concurrent_chats())
```

### Pattern 4: Asynchronous Custom Tools

```python
import asyncio
import aiohttp  # Requires: pip install aiohttp
from createagents import BaseTool, CreateAgent


class AsyncWebTool(BaseTool):
    name = 'async_web_fetch'
    description = 'Fetches web page asynchronously'
    parameters = {
        'type': 'object',
        'properties': {
            'url': {'type': 'string', 'description': 'URL to fetch'}
        },
        'required': ['url'],
    }

    async def execute(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()


# Usage
async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', tools=[AsyncWebTool()]
    )

    response = await agent.chat('Fetch data from https://api.example.com')
    print(response)


asyncio.run(main())
```

______________________________________________________________________

## 🔧 Handler Implementations

### Non-Streaming Handler (Tool Calling Loop)

## 🔧 Internal Handler Architecture (Conceptual)

> **Architectural Note:** The snippets below illustrate the conceptual internal design used by infrastructure adapters (`OpenAIHandler`, `OpenAIStreamHandler`) to orchestrate multi-turn tool loops and streaming metrics recording.

### Non-Streaming Pattern (Tool Calling Loop)

```python
# Conceptual execution loop in non-streaming handlers
class OpenAIHandlerConceptual:
    def __init__(self, client: Any, logger: Any) -> None:
        self._client = client
        self._logger = logger

    async def execute_tool_loop(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> str:
        response_api = await self._client.call_api(
            model, instructions, messages, config, tools
        )
        if getattr(response_api, 'tool_calls', None):
            # Executes tools and loops until the final text response
            pass
        return getattr(response_api, 'output_text', '')
```

### Streaming Pattern with Metrics

```python
# Conceptual streaming pattern with metrics recording
class OpenAIStreamHandlerConceptual:
    def __init__(self, client: Any, recorder: Any) -> None:
        self._client = client
        self._recorder = recorder

    async def handle_stream(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()
        try:
            stream_response = await self._client.call_stream(...)
            async for chunk in stream_response:
                yield chunk
            # Accumulate token metrics and record success
            self._recorder.record_success(model, start_time)
        except Exception as e:
            self._recorder.record_error(model, start_time, e)
            raise
```

______________________________________________________________________

## 🐛 Common Pitfalls

### 1. Forgetting `await` on `chat()`

```python
# ❌ INCORRECT
async def incorrect():
    response = agent.chat('message')  # Returns coroutine without awaiting
    print(response)  # <coroutine object...>


# ✅ CORRECT
async def correct():
    response = await agent.chat('message')  # Awaits and returns result
    print(response)
```

### 2. Blocking the Event Loop

```python
# ❌ INCORRECT (blocking I/O)
async def bad_function():
    time.sleep(10)  # Blocks the entire event loop!


# ✅ CORRECT (non-blocking)
async def good_function():
    await asyncio.sleep(10)  # Yields control back to the event loop
```

### 3. Not using `asyncio.run()`

```python
# ❌ INCORRECT
async def main():
    response = await agent.chat('message')
    print(response)


main()  # RuntimeWarning / Error: coroutine was never awaited

# ✅ CORRECT
asyncio.run(main())
```

### 4. Double-Consuming `StreamingResponseDTO`

When `config={'stream': True}` is active, `await agent.chat()` returns a [`StreamingResponseDTO`](../reference/streaming-api.md).

- **`await response`:** drains the underlying generator and caches the complete string in `_full_response`. Subsequent calls to `await response` return the cached full string.
- **`async for token in response:`** consumes tokens in real-time. A second `async for` on an already exhausted stream terminates immediately without yielding tokens (since `async for` catches `StopAsyncIteration` internally).
- Direct calls to `response.__anext__()` on an exhausted generator explicitly raise `StopAsyncIteration`.

```python
from createagents import CreateAgent


async def demo_streaming():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('message')  # Returns StreamingResponseDTO

    # 1. Consumption via await:
    text1 = await response  # Consumes stream and caches result
    text2 = await response  # Returns cached string (text2 == text1)

    # 2. Consumption via async for:
    stream_resp = await agent.chat('another message')
    async for token in stream_resp:
        print(token, end='')  # Consumes tokens

    # A second immediate iteration on the same stream_resp terminates cleanly:
    async for token in stream_resp:
        pass  # Exits immediately with 0 iterations
```

______________________________________________________________________

## 📊 Performance

### Sequential vs Concurrent Execution

**Sequential**:

```python
async def sequential():
    r1 = await agent.chat('Q1')  # ~2s
    r2 = await agent.chat('Q2')  # ~2s
    r3 = await agent.chat('Q3')  # ~2s
    # Total: ~6s
```

**Concurrent**:

```python
async def concurrent():
    results = await asyncio.gather(
        agent.chat('Q1'),  # ~2s
        agent.chat('Q2'),  # ~2s
        agent.chat('Q3'),  # ~2s
    )
    # Total: ~2s (executed in parallel)
```

______________________________________________________________________

## 🧪 Testing Asynchronous Code

### Unit Tests with Mocks (Fast and Free)

```python
from unittest.mock import AsyncMock, patch
import pytest
from createagents import CreateAgent
from createagents.application.dtos import ChatOutputDTO


@pytest.mark.asyncio
async def test_chat_with_mock():
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = ChatOutputDTO(
        response='Mocked Response'
    )

    with patch(
        'createagents.main.composers.AgentComposer.create_chat_use_case',
        return_value=mock_use_case,
    ):
        agent = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
        response = await agent.chat('Test message')
        assert response == 'Mocked Response'
```

### Integration Tests with Real Providers

> **Warning:** Real provider tests consume API quota and require `OPENAI_API_KEY`. They must be marked with `@pytest.mark.integration`.

```python
import os
import pytest
from createagents import CreateAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_openai_integration():
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip('OPENAI_API_KEY not configured')

    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    response = await agent.chat('Reply with: OK')
    assert 'OK' in response
```

______________________________________________________________________

## 💡 Best Practices

1. **Always use await**: To execute coroutines properly.
2. **Use `asyncio.gather`**: For concurrent agent calls.
3. **Do not block**: Use async libraries (`aiohttp`, `aiofiles`) for I/O.
4. **Handle exceptions**: Wrap async calls in `try/except`.
5. **Proper logging**: Use loggers instead of print statements in async functions.
6. **Test with `pytest-asyncio`**: Mark async test functions with `@pytest.mark.asyncio`.

______________________________________________________________________

## 📚 References

- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Async Generators](https://peps.python.org/pep-0525/)
- [Streaming API Reference](../reference/streaming-api.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-27
