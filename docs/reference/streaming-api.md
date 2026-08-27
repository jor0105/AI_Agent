# API de Streaming

Referência técnica completa da API de streaming do CreateAgents AI.

______________________________________________________________________

## StreamingResponseDTO

**Namespace**: `createagents.application.dtos`

Classe que encapsula um `AsyncGenerator` e fornece interface conveniente para consumo de respostas em streaming.

### Assinatura

```python
class StreamingResponseDTO:
    def __init__(self, generator: AsyncGenerator[str, None]): ...

    async def __anext__(self) -> str: ...
    def __aiter__(self) -> 'StreamingResponseDTO': ...
    def __await__(self) -> Generator[Any, None, str]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
```

### Métodos

#### `__init__(generator: AsyncGenerator[str, None])`

Inicializa o DTO com um gerador assíncrono.

**Parâmetros**:

- `generator`: AsyncGenerator que yield tokens como strings

**Exemplo**:

```python
async def my_generator():
    yield 'Hello'
    yield ' '
    yield 'World'


dto = StreamingResponseDTO(my_generator())
```

#### `__aiter__() -> StreamingResponseDTO`

Retorna iterador para uso em `async for`.

**Retorna**: Self

**Exemplo**:

```python
async def iterate_tokens(dto):
    async for token in dto:
        print(token, end='')
```

#### `async __anext__() -> str`

Retorna próximo token do stream.

**Retorna**: String com próximo token

**Levanta**: `StopAsyncIteration` quando stream termina

**Exemplo**:

```python
async def get_next_token(dto):
    token = await dto.__anext__()
```

#### `__await__() -> Generator`

Permite usar `await` para consumir todo o stream e retornar string completa.

**Retorna**: String com resposta completa

**Exemplo**:

```python
async def consume_all(dto):
    full_response = await dto
    print(full_response)  # "Hello World"
```

#### `__str__() -> str`

Retorna representação em string.

**Retorna**: String completa se consumido, placeholder caso contrário:
`StreamingResponseDTO(not consumed - use "await response")`

**Exemplo**:

```python
print(str(dto))  # "StreamingResponseDTO(not consumed - use "await response")"
```

#### `__repr__() -> str`

Retorna representação para debugging com status de consumo e comprimento.

______________________________________________________________________

## Uso Completo

### Padrão 1: Await para String Completa

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )
    response = await agent.chat('Olá')  # Retorna StreamingResponseDTO
    text = (
        await response
    )  # Consome stream e retorna string completa (com cache)
    print(text)


asyncio.run(main())
```

### Padrão 2: Async For para Streaming

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )
    response = await agent.chat('Conte uma história')

    async for token in response:
        print(token, end='', flush=True)
    print()


asyncio.run(main())
```

### Padrão 3: Combinar Acumulação e Exibição

```python
import asyncio
from createagents import CreateAgent


async def accumulate_and_display():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )
    response = await agent.chat('Liste 5 dicas')

    accumulated = ''
    async for token in response:
        accumulated += token
        print(token, end='', flush=True)

    print(f'\n\nTotal caracteres: {len(accumulated)}')


asyncio.run(accumulate_and_display())
```

______________________________________________________________________

## Propriedades Internas

| Propriedade      | Tipo                        | Descrição                                        |
| ---------------- | --------------------------- | ------------------------------------------------ |
| `_generator`     | `AsyncGenerator[str, None]` | Gerador assíncrono de tokens                     |
| `_consumed`      | `bool`                      | Flag indicando se o stream já foi consumido      |
| `_full_response` | `str`                       | String concatenada e armazenada em cache interno |

______________________________________________________________________

## Semântica de Consumo e Iteração

### Consumo e Cache

- **Via `await response`**: Consome o gerador assíncrono por completo e armazena o texto concatenado no cache interno `_full_response`. Chamadas repetidas a `await response` retornam imediatamente o texto completo em cache.
- **Via `async for token in response:`**: Consome os tokens progressivamente até esgotar o gerador, marcando `_consumed = True`.
- **Segundo `async for` após o consumo**: Como o gerador subjacente foi esgotado, uma segunda iteração `async for` termina imediatamente produzindo 0 itens (o `async for` captura `StopAsyncIteration` internamente e encerra sem erro para o chamador).
- **Chamada direta a `response.__anext__()`**: Se chamada diretamente em um gerador já consumido, lança explicitamente `StopAsyncIteration`.

______________________________________________________________________

## Exceções

### StopAsyncIteration

Levantada quando iteração termina.

```python
async def demo_loop(response):
    async for token in response:
        print(token)
    # StopAsyncIteration é capturada internamente ao final do gerador
```

______________________________________________________________________

## Veja Também

- [Guia de Streaming](../user-guide/streaming-guide.md)
- [Guia Async](../dev-guide/async-guide.md)
- [API Reference](api.md)

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-25
