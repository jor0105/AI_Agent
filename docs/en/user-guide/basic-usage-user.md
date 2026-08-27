# Basic User Guide

Learn how to quickly create and interact with AI agents.

## First Agent

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='You are a helpful assistant',
)
```

## Conversing (Multi-Turn Chat)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        instructions='You are a helpful assistant',
    )

    response1 = await agent.chat('Hello! How are you?')
    response2 = await agent.chat('What is the capital of Japan?')
    response3 = await agent.chat('And what is its population?')

    for response in [response1, response2, response3]:
        print(response)


asyncio.run(main())
```

## Configurations

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
config = agent.get_configs()
print(f'Model: {config["model"]}')
print(f'History: {len(config["history"])} messages')
```

## Clear History

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
agent.clear_history()
```

## Streaming (Real-Time Responses)

### Option 1: Await (Receive full response)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
    )
    # Receives the complete response
    response = await agent.chat('Write a poem')
    print(response)


asyncio.run(main())
```

### Option 2: Async For (Token-by-token streaming)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        config={'stream': True},
    )
    # Receives tokens in real time
    response = await agent.chat('Tell a story')
    async for token in response:
        print(token, end='', flush=True)
    print()  # Final newline


asyncio.run(main())
```

> ℹ️ **Note**: Streaming is enabled via the `stream` parameter in `config` (e.g. `config={"stream": True}`). By default it is `False`. Both providers (OpenAI and Ollama) support streaming.

## Customizing Instructions

```python
from createagents import CreateAgent

agent_formal = CreateAgent(
    provider='openai', model='YOUR_MODEL', instructions='Use formal language'
)
agent_technical = CreateAgent(
    provider='openai', model='YOUR_MODEL', instructions='Python technical expert'
)
```

## Advanced Configurations

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    config={'temperature': 0.7, 'max_tokens': 2000},
    history_max_size=50,
)
```

## Tools

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', tools=['currentdate']
    )
    response = await agent.chat('What day is today?')
    print(response)


asyncio.run(main())
```

## Checking Available Tools

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
all_tools = agent.get_all_available_tools()
for name, description in all_tools.items():
    print(f'• {name}: {description[:50]}...')
```

## Creating Custom Tools

```python
from createagents import BaseTool


class WordCountTool(BaseTool):
    name = 'word_count'
    description = 'Counts the number of words in a text'
    parameters = {
        'type': 'object',
        'properties': {
            'text': {
                'type': 'string',
                'description': 'Text to count words from',
            }
        },
        'required': ['text'],
    }

    def execute(self, text: str) -> str:
        return str(len(text.split()))
```

## Metrics

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
metrics = agent.get_metrics()
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

## Next Steps

- [Examples](examples-user.md)
- [FAQ](faq-user.md)
