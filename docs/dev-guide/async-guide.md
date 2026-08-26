# Guia de Programação Assíncrona

Este guia explica como a arquitetura assíncrona funciona no CreateAgents AI.

______________________________________________________________________

## 🔄 Por Que Async?

O CreateAgents AI usa programação assíncrona para:

- **Streaming**: Tokens em tempo real das APIs (OpenAI/Ollama)
- **Tools**: Execução não-bloqueante de ferramentas
- **Performance**: Múltiplas chamadas concorrentes

______________________________________________________________________

## 🎯 Componentes Assíncronos

### ChatRepository (Interface)

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
        """Chat assíncrono que retorna resposta completa ou AsyncGenerator."""
        pass

    @abstractmethod
    def get_metrics(self) -> list[ChatMetrics]:
        """Retorna a lista de métricas coletadas durante as interações."""
        pass
```

### ChatAdapter (Implementação)

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

### Stream Handlers

#### OpenAIStreamHandler

```python
class OpenAIStreamHandler(BaseStreamHandler):
    async def handle_stream(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> AsyncGenerator[str, None]:
        # Comunicação assíncrona via Responses API com suporte a tool calls
        stream_response = await self.__client.call_api(...)

        async for event in stream_response:
            if event.type == 'response.output_text.delta':
                yield event.delta
```

#### OllamaStreamHandler

```python
class OllamaStreamHandler(BaseStreamHandler):
    async def handle_stream(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> AsyncGenerator[str, None]:
        async for chunk in client.chat(
            model=model,
            messages=messages,
            stream=True,
            ...
        ):
            if chunk.get('message', {}).get('content'):
                yield chunk['message']['content']
```

______________________________________________________________________

## 🛠️ Execução Assíncrona de Ferramentas

### ToolExecutor

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
            # Suporta funções de execução assíncronas ou síncronas em threadpool
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

## 🔄 Fluxo Assíncrono Completo

### Sem Ferramentas

```
User: await agent.chat("mensagem")
  → ChatWithAgentUseCase.execute() [async]
      → ChatRepository.chat() [async]
          → OpenAIStreamHandler.handle_stream() [async se stream=True]
              → async for chunk in openai_stream:
                  → yield chunk
          ← AsyncGenerator[str, None]
      ← StreamingResponseDTO
  ← await response (string completa) ou async for token in response
```

### Com Ferramentas

```
User: await agent.chat("Que dia é hoje?")
  → ChatWithAgentUseCase.execute() [async]
      → ChatRepository.chat() [async]
          → OpenAIStreamHandler / OpenAIHandler [async]
              → Detecta tool_calls na resposta da API
              → Para cada tool_call:
                  → ToolExecutor.execute_tool(tool_name, **args) [async]
                      ← ToolExecutionResult
              → Próxima iteração com tool results no histórico
              → yield token (ou retorna resposta final)
          ← StreamingResponseDTO (se stream=True) ou str (se stream=False)
  ← await response
```

______________________________________________________________________

## 💡 Padrões de Uso

### Padrão 1: Consumo Simples (Await)

```python
import asyncio


async def simple_chat():
    from createagents import CreateAgent

    agent = CreateAgent(provider='openai', model='gpt-4')
    response = await agent.chat('Olá')  # Aguarda string completa
    print(response)


asyncio.run(simple_chat())
```

### Padrão 2: Streaming Manual (Async For)

```python
import asyncio


async def streaming_chat():
    from createagents import CreateAgent

    agent = CreateAgent(provider='openai', model='gpt-4')
    response = await agent.chat('Conte uma história')

    async for token in response:
        print(token, end='', flush=True)
    print()


asyncio.run(streaming_chat())
```

### Padrão 3: Múltiplas Chamadas Concorrentes

```python
import asyncio


async def concurrent_chats():
    from createagents import CreateAgent

    agent1 = CreateAgent(provider='openai', model='gpt-4')
    agent2 = CreateAgent(provider='openai', model='gpt-4')

    # Executar simultaneamente
    results = await asyncio.gather(
        agent1.chat('Pergunta 1'),
        agent2.chat('Pergunta 2'),
    )

    print(results[0])
    print(results[1])


asyncio.run(concurrent_chats())
```

### Padrão 4: Ferramentas Assíncronas

```python
from createagents import BaseTool
import asyncio
import aiohttp


class AsyncWebTool(BaseTool):
    name = 'async_web_fetch'
    description = 'Busca dados da web assincronamente'
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


# Uso
async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', tools=[AsyncWebTool()]
    )

    response = await agent.chat('Busque dados de https://api.example.com')
    print(response)  # Retorna a string diretamente quando stream=False


asyncio.run(main())
```

______________________________________________________________________

## 🔧 Implementação de Handlers

### Handler Não-Streaming (Tool Calling Loop)

```python
class OpenAIHandler:
    async def execute_tool_loop(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> str:
        # Loop de chamadas e execução de ferramentas
        response_api = await self.__client.call_api(
            model, instructions, messages, config, session.schemas
        )
        if ToolCallParser.has_tool_calls(response_api):
            await run_tool_calls(response_api, messages, session.executor, self.__logger)
            # Continua o loop até resposta final...
        return response_api.output_text
```

### Handler de Streaming com Métricas

```python
class OpenAIStreamHandler(BaseStreamHandler):
    async def handle_stream(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()
        totals = StreamUsageTotals()

        try:
            stream_response = await self.__client.call_api(...)
            async for event in stream_response:
                if event.type == 'response.output_text.delta':
                    yield event.delta

            # Acumula uso de tokens e grava métricas de sucesso
            self.record_stream_success(model, start_time, totals, iteration)
        except Exception as e:
            self.record_stream_error(model, start_time, e)
            raise
```

______________________________________________________________________

## 🐛 Armadilhas Comuns

### 1. Esquecer await no chat()

```python
# ❌ ERRADO
response = agent.chat('mensagem')  # Retorna coroutine sem await
print(response)  # <coroutine object...>

# ✅ CORRETO
response = await agent.chat(
    'mensagem'
)  # Aguarda a coroutine e retorna o resultado
print(response)
```

### 2. Bloquear Loop de Eventos

```python
# ❌ ERRADO (blocking I/O)
async def bad_function():
    time.sleep(10)  # Bloqueia todo o loop!


# ✅ CORRETO (non-blocking)
async def good_function():
    await asyncio.sleep(10)  # Permite outras tasks
```

### 3. Não Usar asyncio.run()

```python
# ❌ ERRADO
async def main():
    response = await agent.chat('mensagem')
    print(response)


main()  # Erro! Coroutine não executada

# ✅ CORRETO
asyncio.run(main())
```

### 4. Consumir StreamingResponseDTO Duas Vezes

Quando `config={'stream': True}` está ativado, `await agent.chat()` retorna um [`StreamingResponseDTO`](../reference/streaming-api.md). Ele é um gerador de uso único:

```python
agent = CreateAgent(
    provider='openai', model='gpt-4', config={'stream': True}
)
response = await agent.chat('mensagem')  # Retorna StreamingResponseDTO

# ❌ ERRADO: consumir o generator duas vezes
text1 = await response  # Consome stream completamente
text2 = await response  # Já consumido! text2 = ""

# ✅ CORRETO: consumir uma vez ou iterar com async for
text = await response  # Consumir apenas uma vez
```

______________________________________________________________________

## 📊 Performance

### Concorrência vs Sequencial

**Sequencial**:

```python
async def sequential():
    r1 = await agent.chat('Q1')  # 2s
    r2 = await agent.chat('Q2')  # 2s
    r3 = await agent.chat('Q3')  # 2s
    # Total: 6s
```

**Concorrente**:

```python
async def concurrent():
    results = await asyncio.gather(
        agent.chat('Q1'),  # 2s
        agent.chat('Q2'),  # 2s
        agent.chat('Q3'),  # 2s
    )
    # Total: ~2s (paralelizado)
```

______________________________________________________________________

## 🧪 Testando Código Assíncrono

```python
import pytest


@pytest.mark.asyncio
async def test_chat():
    agent = CreateAgent(provider='openai', model='gpt-4')
    response = await agent.chat('Test message')
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_streaming():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )
    response = await agent.chat('Test')

    tokens = []
    async for token in response:
        tokens.append(token)

    assert len(tokens) > 0
```

______________________________________________________________________

## 💡 Best Practices

1. **Sempre use await**: Para executar coroutines
2. **Use asyncio.gather**: Para chamadas concorrentes
3. **Não bloqueie**: Use bibliotecas async (aiohttp, aiofiles)
4. **Trate exceções**: try/except em código async
5. **Logging apropriado**: Use logger em funções async
6. **Teste com pytest-asyncio**: Marque tests com `@pytest.mark.asyncio`

______________________________________________________________________

## 📚 Referências

- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Async Generators](https://peps.python.org/pep-0525/)
- [API de Streaming](../reference/streaming-api.md)

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 07/08/2026
