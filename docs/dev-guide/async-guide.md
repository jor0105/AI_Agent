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

Os adaptadores de infraestrutura delegam chamadas com streaming para handlers especializados (`OpenAIStreamHandler`, `OllamaStreamHandler`), que retornam um gerador assíncrono `AsyncGenerator[str, None]` emitindo tokens em tempo real.

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

    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    response = await agent.chat('Olá')  # Aguarda string completa
    print(response)


asyncio.run(simple_chat())
```

### Padrão 2: Streaming Manual (Async For)

```python
import asyncio
from createagents import CreateAgent


async def streaming_chat():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('Conte uma história')

    async for token in response:
        print(token, end='', flush=True)
    print()


asyncio.run(streaming_chat())
```

### Padrão 3: Múltiplas Chamadas Concorrentes

```python
import asyncio
from createagents import CreateAgent


async def concurrent_chats():
    agent1 = CreateAgent(provider='openai', model='YOUR_MODEL')
    agent2 = CreateAgent(provider='openai', model='YOUR_MODEL')

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
import asyncio
import aiohttp  # Requer instalação: pip install aiohttp
from createagents import BaseTool, CreateAgent


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
        provider='openai', model='YOUR_MODEL', tools=[AsyncWebTool()]
    )

    response = await agent.chat('Busque dados de https://api.example.com')
    print(response)  # Retorna a string diretamente quando stream=False


asyncio.run(main())
```

______________________________________________________________________

## 🔧 Arquitetura Interna de Handlers (Conceitual)

> **Nota de Arquitetura:** Os exemplos abaixo ilustram o padrão arquitetural interno implementado pelos adaptadores de infraestrutura (`OpenAIHandler`, `OpenAIStreamHandler`) para orquestrar chamadas e acumulação de métricas.

### Padrão Não-Streaming (Loop de Tool Calling)

```python
# Arquitetura conceitual do loop de execução em handlers não-streaming
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
        # Loop de chamadas e execução de ferramentas
        response_api = await self._client.call_api(
            model, instructions, messages, config, tools
        )
        if getattr(response_api, 'tool_calls', None):
            # Executa chamadas de ferramentas e reitera até resposta final
            pass
        return getattr(response_api, 'output_text', '')
```

### Padrão de Streaming com Métricas

```python
# Arquitetura conceitual de streaming com gravação de métricas
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
            # Acumula uso de tokens e grava métricas de sucesso
            self._recorder.record_success(model, start_time)
        except Exception as e:
            self._recorder.record_error(model, start_time, e)
            raise
```

______________________________________________________________________

## 🐛 Armadilhas Comuns

### 1. Esquecer await no chat()

```python
# ❌ ERRADO
async def incorreto():
    response = agent.chat('mensagem')  # Retorna coroutine sem await
    print(response)  # <coroutine object...>


# ✅ CORRETO
async def correto():
    response = await agent.chat('mensagem')  # Aguarda a coroutine e retorna
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

### 4. Consumo Duplo de StreamingResponseDTO

Quando `config={'stream': True}` está ativo, `await agent.chat()` retorna um [`StreamingResponseDTO`](../reference/streaming-api.md).

- **`await response`:** consome o gerador subjacente e armazena o texto completo em cache (`_full_response`). Chamadas subsequentes de `await response` retornam a mesma string já em cache.
- **`async for token in response:`** consome os tokens em tempo real. Uma segunda tentativa de iterar com `async for` termina imediatamente com 0 itens gerados (pois o loop trata o esgotamento internamente).
- Uma chamada manual direta a `await response.__anext__()` após o término do gerador lança `StopAsyncIteration`.

```python
from createagents import CreateAgent


async def demo_streaming():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', config={'stream': True}
    )
    response = await agent.chat('mensagem')  # Retorna StreamingResponseDTO

    # 1. Consumo via await (cache):
    text1 = await response  # Consome o stream e armazena no cache
    text2 = await response  # Retorna o mesmo texto em cache (text2 == text1)

    # 2. Consumo via async for:
    stream_resp = await agent.chat('outra mensagem')
    async for token in stream_resp:
        print(token, end='')

    # Segunda iteração termina imediatamente sem produzir novos tokens:
    async for token in stream_resp:
        pass  # Conclui imediatamente com 0 itens
```

______________________________________________________________________

## 📊 Performance: Concorrência com asyncio.gather

Compare chamadas sequenciais versus concorrentes:

```python
# Sequencial (~6s para 3 chamadas de 2s)
async def sequential():
    r1 = await agent.chat('Q1')
    r2 = await agent.chat('Q2')
    r3 = await agent.chat('Q3')


# Concorrente (~2s paralelizado)
async def concurrent():
    r1, r2, r3 = await asyncio.gather(
        agent.chat('Q1'), agent.chat('Q2'), agent.chat('Q3')
    )
```

______________________________________________________________________

## 🧪 Testando Código Assíncrono

### Testes Unitários com Mock (Sem Custos de API)

```python
from unittest.mock import AsyncMock, patch
import pytest
from createagents import CreateAgent
from createagents.application.dtos import ChatOutputDTO


@pytest.mark.asyncio
async def test_chat_with_mock():
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = ChatOutputDTO(
        response='Resposta simulada'
    )

    with patch(
        'createagents.main.composers.AgentComposer.create_chat_use_case',
        return_value=mock_use_case,
    ):
        agent = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
        response = await agent.chat('Mensagem de teste')
        assert response == 'Resposta simulada'
```

### Testes de Integração com Provedor Real

> **Atenção:** Testes de integração gastam quota externa e requerem `OPENAI_API_KEY`. Devem ser marcados com `@pytest.mark.integration`.

```python
import os
import pytest
from createagents import CreateAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_openai_integration():
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip('OPENAI_API_KEY não definida')

    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    response = await agent.chat('Responda OK')
    assert 'OK' in response
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

**Versão:** 0.3.0 | **Atualização:** 2026-08-27
