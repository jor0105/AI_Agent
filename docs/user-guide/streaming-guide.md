# Guia de Streaming

Este guia explica como receber respostas do agente em tempo real.

______________________________________________________________________

## 💡 O que é Streaming?

Streaming permite que você veja a resposta aparecendo **palavra por palavra** em tempo real, como se o agente estivesse digitando. Isso deixa a experiência mais natural e interativa.

**Sem streaming**: Você espera 5 segundos e recebe a resposta completa de uma vez.
**Com streaming**: As palavras aparecem imediatamente, conforme o agente gera a resposta.

______________________________________________________________________

## 🚀 Como Usar

Existem duas formas de receber respostas do agente:

### 1️⃣ Receber a Resposta Completa (Mais Simples)

Use `await` para esperar a resposta completa:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='gpt-4')

    # Espera a resposta completa
    resposta = await agent.chat('Escreva um poema')
    print(resposta)


asyncio.run(main())
```

### 2️⃣ Ver Palavra por Palavra (Streaming em Tempo Real)

Use `async for` para ver cada palavra aparecer (requer `config={'stream': True}`):

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        config={'stream': True},
    )

    resposta = await agent.chat('Conte uma história')

    # Mostra palavra por palavra
    async for palavra in resposta:
        print(palavra, end='', flush=True)
    print()  # Nova linha no final


asyncio.run(main())
```

> 💡 **Dica**: Use a opção 2 para chatbots ou interfaces onde você quer mostrar o agente "pensando".

______________________________________________________________________

## 📚 Exemplos Práticos

### Exemplo 1: Chatbot Interativo

Crie um chatbot que mostra as palavras aparecendo:

```python
import asyncio
from createagents import CreateAgent


async def chat_interface():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        config={'stream': True},
    )

    while True:
        user_input = input('Você: ')
        if user_input.lower() in ['sair', 'exit']:
            break

        print('Agente: ', end='', flush=True)
        resposta = await agent.chat(user_input)

        # Mostra palavra por palavra
        async for palavra in resposta:
            print(palavra, end='', flush=True)
        print('\n')


asyncio.run(chat_interface())
```

### Exemplo 2: Perguntas Simples

Para perguntas diretas, use `await` (mais simples):

```python
import asyncio
from createagents import CreateAgent


async def perguntas_simples():
    agent = CreateAgent(provider='openai', model='gpt-4')

    # Pergunta direta
    resposta = await agent.chat('Qual a capital do Brasil?')
    print(f'Resposta: {resposta}')


asyncio.run(perguntas_simples())
```

______________________________________________________________________

## ⚙️ Ativando e Desativando Streaming

### Ativar Streaming

Para utilizar streaming em tempo real, passe `config={"stream": True}` na criação do agente:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': True}
    )

    resposta = await agent.chat('Conte uma história')
    async for palavra in resposta:
        print(palavra, end='', flush=True)


asyncio.run(main())
```

### Desativar Streaming

Se preferir esperar a resposta completa, desative o streaming:

```python
import asyncio
from createagents import CreateAgent


async def main():
    # Desabilita streaming
    agent = CreateAgent(
        provider='openai', model='gpt-4', config={'stream': False}
    )

    # Recebe tudo de uma vez
    resposta = await agent.chat('Olá')
    print(resposta)


asyncio.run(main())
```

______________________________________________________________________

### Usar com Ollama (Modelos Locais)

```python
import asyncio
from createagents import CreateAgent


async def ollama_streaming():
    agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        config={'stream': True},
    )

    resposta = await agent.chat('Explique machine learning')
    async for palavra in resposta:
        print(palavra, end='', flush=True)
    print()


asyncio.run(ollama_streaming())
```

**Funciona igual!** Não importa se usa OpenAI ou Ollama, o streaming funciona da mesma forma.

______________________________________________________________________

## 🛠️ Usando Ferramentas

O streaming funciona normalmente mesmo quando o agente usa ferramentas:

```python
import asyncio
from createagents import CreateAgent


async def exemplo_com_ferramentas():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        tools=['currentdate'],
        config={'stream': True},
    )

    print('Perguntando sobre datas...\n')
    resposta = await agent.chat('Que dia é hoje?')

    # O agente usa a ferramenta e responde em streaming
    async for palavra in resposta:
        print(palavra, end='', flush=True)
    print()


asyncio.run(exemplo_com_ferramentas())
```

______________________________________________________________________

## 📊 Streaming e Métricas

Métricas são coletadas automaticamente, independentemente do modo de consumo:

```python
import asyncio
from createagents import CreateAgent


async def streaming_with_metrics():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        config={'stream': True},
    )

    # Streaming
    response = await agent.chat('Conte uma piada')
    async for token in response:
        print(token, end='')
    print('\n')

    # Métricas ainda são gravadas
    metrics = agent.get_metrics()
    if metrics:
        print(f'\nLatência: {metrics[-1].latency_ms}ms')
        print(f'Tokens: {metrics[-1].tokens_used}')


asyncio.run(streaming_with_metrics())
```

______________________________________________________________________

## 💡 Dicas

### 1. Para Perguntas Rápidas

Use `await` para receber a resposta completa envolvendo em uma função `async`:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='gpt-4')
    resposta = await agent.chat('Explique o que é Python')
    print(resposta)


asyncio.run(main())
```

______________________________________________________________________

## 📚 Próximos Passos

- [Uso da CLI](cli-usage.md) - Interface interativa
- [Exemplos Práticos](examples-user.md) - Mais exemplos de uso
- [FAQ](faq-user.md) - Perguntas frequentes

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 07/08/2026
