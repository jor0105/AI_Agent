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
async for token in dto:
    print(token, end='')
```

#### `async __anext__() -> str`

Retorna próximo token do stream.

**Retorna**: String com próximo token

**Levanta**: `StopAsyncIteration` quando stream termina

**Exemplo**:

```python
token = await dto.__anext__()
```

#### `__await__() -> Generator`

Permite usar `await` para consumir todo o stream e retornar string completa.

**Retorna**: String com resposta completa

**Exemplo**:

```python
full_response = await dto
print(full_response)  # "Hello World"
```

#### `__str__() -> str`

Retorna representação em string.

**Retorna**: String completa se consumido, placeholder caso contrário

**Exemplo**:

```python
print(str(dto))  # "StreamingResponseDTO(not consumed - use 'await response')"
```

#### `__repr__() -> str`

Retorna representação para debugging.

**Retorna**: String com status e comprimento

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
    response = await agent.chat('Olá')  # StreamingResponseDTO
    text = await response  # String completa
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

| Propriedade      | Tipo                      | Descrição               |
| ---------------- | ------------------------- | ----------------------- |
| `_generator`     | AsyncGenerator[str, None] | Gerador de tokens       |
| `_consumed`      | bool                      | Se stream foi consumido |
| `_full_response` | str                       | Resposta acumulada      |

______________________________________________________________________

## Exceções

### StopAsyncIteration

Levantada quando iteração termina.

```python
async for token in response:
    print(token)
# StopAsyncIteration é levantada automaticamente ao final
```

______________________________________________________________________

## Veja Também

- [Guia de Streaming](../user-guide/streaming-guide.md)
- [Guia Async](../dev-guide/async-guide.md)
- [API Reference](api.md)

______________________________________________________________________

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
