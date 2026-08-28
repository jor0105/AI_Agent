# Guia de Uso Básico do Usuário

Aprenda a criar e interagir com agentes de IA rapidamente.

## Primeiro Agente

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='Você é um assistente útil',
)
```

## Conversando

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        instructions='Você é um assistente útil',
    )

    response1 = await agent.chat('Olá! Como você está?')
    response2 = await agent.chat('Qual é a capital do Brasil?')
    response3 = await agent.chat('E a população?')

    for response in [response1, response2, response3]:
        print(response)


asyncio.run(main())
```

## Configurações

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
config = agent.get_configs()
print(f'Modelo: {config["model"]}')
print(f'Histórico: {len(config["history"])} mensagens')
```

## Limpar Histórico

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
agent.clear_history()
```

## Streaming (Respostas em Tempo Real)

### Opção 1: Await (Receber resposta completa)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
    )
    # Recebe a resposta completa
    response = await agent.chat('Escreva um poema')
    print(response)


asyncio.run(main())
```

### Opção 2: Async For (Streaming token por token)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        config={'stream': True},
    )
    # Recebe tokens em tempo real
    response = await agent.chat('Conte uma história')
    async for token in response:
        print(token, end='', flush=True)
    print()  # Nova linha no final


asyncio.run(main())
```

> ℹ️ **Nota**: Streaming é controlado pelo parâmetro `stream` em `config` (ex: `config={"stream": True}`). Por padrão é `False`. Ambos os provedores (OpenAI e Ollama) suportam streaming.

## Personalizando

```python
from createagents import CreateAgent

agent_formal = CreateAgent(
    provider='openai', model='YOUR_MODEL', instructions='Use linguagem formal'
)
agent_tecnico = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='Especialista em Python',
)
```

## Configurações Avançadas

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    config={'temperature': 0.7, 'max_tokens': 2000},
    history_max_size=50,
)
```

## Ferramentas

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', tools=['currentdate']
    )
    response = await agent.chat('Que dia é hoje?')
    print(response)


asyncio.run(main())
```

## Verificar Ferramentas Disponíveis

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
all_tools = agent.get_all_available_tools()
for name, description in all_tools.items():
    print(f'• {name}: {description[:50]}...')
```

## Criar Ferramentas Customizadas

```python
from createagents import BaseTool


class WordCountTool(BaseTool):
    name = 'word_count'
    description = 'Conta o número de palavras em um texto'
    parameters = {
        'type': 'object',
        'properties': {
            'text': {
                'type': 'string',
                'description': 'Texto a ser analisado',
            }
        },
        'required': ['text'],
    }

    def execute(self, text: str) -> str:
        return str(len(text.split()))
```

## Métricas

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
metrics = agent.get_metrics()
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

## Próximos Passos

- [Exemplos](examples-user.md)
- [FAQ](faq-user.md)
