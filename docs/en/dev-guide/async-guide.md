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
    agent = CreateAgent(provider='openai', model='gpt-4')
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
        provider='openai', model='gpt-4', config={'stream': True}
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
    agent1 = CreateAgent(provider='openai', model='gpt-4')
    agent2 = CreateAgent(provider='openai', model='gpt-4')

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
import aiohttp
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
        async with (
            aiohttp.ClientSession() as session,
            session.get(url) as response,
        ):
            return await response.text()
```

______________________________________________________________________

## 🐛 Common Pitfalls

1. **Forgetting `await` on `chat()`**: Calling `agent.chat(...)` returns a coroutine. You must `await` it.
2. **Blocking the Event Loop**: Never use `time.sleep()` in async functions; use `await asyncio.sleep()`.
3. **Double-Consuming `StreamingResponseDTO`**: The response generator is single-use.

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
