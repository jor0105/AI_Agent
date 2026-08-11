# Guia de Uso Básico do Usuário

Aprenda a criar e interagir com agentes de IA rapidamente.

## Primeiro Agente

```python
from createagents import CreateAgent
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você é um assistente útil"
)
```

## Conversando

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        instructions="Você é um assistente útil"
    )

    response1 = await agent.chat("Olá! Como você está?")
    response2 = await agent.chat("Qual é a capital do Brasil?")
    response3 = await agent.chat("E a população?")

    for response in [response1, response2, response3]:
        print(response)

asyncio.run(main())
```

## Configurações

```python
config = agent.get_configs()
print(f"Modelo: {config['model']}")
print(f"Histórico: {len(config['history'])} mensagens")
```

## Limpar Histórico

```python
agent.clear_history()
```

## Streaming (Respostas em Tempo Real)

### Opção 1: Await (Receber resposta completa)

```python
import asyncio

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
    )
    # Recebe a resposta completa
    response = await agent.chat("Escreva um poema")
    print(response)

asyncio.run(main())
```

### Opção 2: Async For (Streaming token por token)

```python
import asyncio

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
    )
    # Recebe tokens em tempo real
    response = await agent.chat("Conte uma história")
    async for token in response:
        print(token, end='', flush=True)
    print()  # Nova linha no final

asyncio.run(main())
```

> ℹ️ **Nota**: Streaming é controlado pelo parâmetro `stream` em `config` (ex: `config={"stream": True}`). Por padrão é `False`. Ambos os provedores (OpenAI e Ollama) suportam streaming.

## Personalizando

```python
agent_formal = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Use linguagem formal"
)
agent_tecnico = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Especialista em Python"
)
```

## Configurações Avançadas

```python
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    config={"temperature": 0.7, "max_tokens": 2000},
    history_max_size=50
)
```

## Ferramentas

```python
import asyncio

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["currentdate"]
    )
    response = await agent.chat("Que dia é hoje?")
    print(response)

asyncio.run(main())
```

## Verificar Ferramentas Disponíveis

```python
agent = CreateAgent(provider="openai", model="gpt-4")
all_tools = agent.get_all_available_tools()
for name, description in all_tools.items():
    print(f"• {name}: {description[:50]}...")
```

## Criar Ferramentas Customizadas

```python
from createagents import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Realiza cálculos matemáticos"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Expressão matemática"
            }
        },
        "required": ["expression"]
    }
    def execute(self, expression: str) -> str:
        return str(eval(expression))
```

## Métricas

```python
agent = CreateAgent(provider="openai", model="gpt-4")
metrics = agent.get_metrics()
agent.export_metrics_json("metrics.json")
agent.export_metrics_prometheus("metrics.prom")
```

## Próximos Passos

- [Exemplos](examples-user.md)
- [FAQ](faq-user.md)
