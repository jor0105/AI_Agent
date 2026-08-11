# Exemplos Práticos de Uso

Veja casos reais de uso do Create Agents AI.

## Assistente Educacional

```python
import asyncio
from createagents import CreateAgent

async def main():
    professor = CreateAgent(
        provider="openai",
        model="gpt-4",
        name="Professor Virtual",
        instructions="Você é um professor didático."
    )

    resposta = await professor.chat("Explique recursão em programação")
    print(resposta)

asyncio.run(main())
```

## Assistente Corporativo

```python
import asyncio
from createagents import CreateAgent

async def main():
    assistente = CreateAgent(
        provider="openai",
        model="gpt-4",
        name="Assistente Executivo",
        instructions="Use linguagem formal.",
        tools=["currentdate"]
    )

    resposta = await assistente.chat("Que dia é hoje? Preciso agendar uma reunião")
    print(resposta)

asyncio.run(main())
```

## Assistente de Programação

```python
import asyncio
from createagents import CreateAgent

async def main():
    code_expert = CreateAgent(
        provider="openai",
        model="gpt-4",
        name="Python Expert",
        instructions="Especialista em Python."
    )

    codigo = await code_expert.chat("Crie uma função que valida CPF brasileiro.")
    print(codigo)

asyncio.run(main())
```

## Tradutor Profissional

```python
import asyncio
from createagents import CreateAgent

async def main():
    tradutor = CreateAgent(
        provider="openai",
        model="gpt-4",
        name="Tradutor Especializado",
        instructions="Você é um tradutor profissional."
    )

    resposta = await tradutor.chat(
        "Traduza para inglês: 'A arquitetura clean separa as regras de negócio da infraestrutura.'"
    )
    print(resposta)

asyncio.run(main())
```

## Analista de Dados

```python
import asyncio
from createagents import CreateAgent

async def main():
    analista = CreateAgent(
        provider="ollama",
        model="llama3.2",
        name="Data Analyst",
        instructions="Forneça insights acionáveis."
    )

    dados = "Vendas Q1: Jan=100k, Fev=150k, Mar=120k"
    resposta = await analista.chat(f"Analise estes dados: {dados}")
    print(resposta)

asyncio.run(main())
```

## Chatbot Interativo (Use a CLI!)

**Recomendado**: Para chatbots interativos, use a **CLI integrada**:

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Assistente Amigável",
)

# Inicia CLI interativa
agent.start_cli()
```

A CLI oferece:

- Interface colorida e formatada
- Comandos `/help`, `/metrics`, `/configs`, `/tools`, `/clear`
- Streaming em tempo real
- Indicadores de status

📖 [Guia completo da CLI](cli-usage.md)

### Chat Simples (Loop Manual)

```python
import asyncio

async def main():
    chatbot = CreateAgent(
        provider="openai",
        model="gpt-4",
        name="Chatbot Simples",
        config={"stream": True},
    )

    print("Digite 'sair' para encerrar.\n")
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break

        # Streaming
        response = await chatbot.chat(user_input)
        print("Bot: ", end='', flush=True)
        async for token in response:
            print(token, end='', flush=True)
        print("\n")

asyncio.run(main())
```

## Agente Local com Ollama

```python
import asyncio
from createagents import CreateAgent

async def main():
    agente_local = CreateAgent(
        provider="ollama",
        model="llama3.2",
        name="Assistente Privado",
        instructions="Você é um assistente local."
    )

    resposta = await agente_local.chat("Explique machine learning em termos simples")
    print(resposta)

asyncio.run(main())
```

## Streaming em Tempo Real

```python
import asyncio

async def streaming_example():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        config={"stream": True},
    )

    print("Escrevendo artigo em tempo real:\n")
    response = await agent.chat("Escreva um artigo sobre Clean Architecture")

    # Exibe token por token
    async for token in response:
        print(token, end='', flush=True)
    print("\n\n--- Finalizado ---")

asyncio.run(streaming_example())
```

## Streaming com Ollama

```python
import asyncio

async def ollama_streaming():
    local_agent = CreateAgent(
        provider="ollama",
        model="llama3.2",
        name="Assistente Local",
        config={"stream": True},
    )

    response = await local_agent.chat("Explique o que é LLM")
    async for chunk in response:
        print(chunk, end='', flush=True)
    print()

asyncio.run(ollama_streaming())
```

## Próximos Passos

- [Guia de Streaming](streaming-guide.md)
- [Uso da CLI](cli-usage.md)
- [FAQ](faq-user.md)
