# Practical Usage Examples

Real-world scenarios and integration patterns for Create Agents AI.

## Educational Assistant

```python
import asyncio
from createagents import CreateAgent


async def main():
    professor = CreateAgent(
        provider='openai',
        model='gpt-4',
        name='Virtual Professor',
        instructions='You are a didactic teacher who explains complex concepts simply.',
    )

    response = await professor.chat('Explain recursion in programming')
    print(response)


asyncio.run(main())
```

## Corporate Assistant

```python
import asyncio
from createagents import CreateAgent


async def main():
    assistant = CreateAgent(
        provider='openai',
        model='gpt-4',
        name='Executive Assistant',
        instructions='Use formal business communication.',
        tools=['currentdate'],
    )

    response = await assistant.chat(
        'What day is today? I need to schedule an executive review.'
    )
    print(response)


asyncio.run(main())
```

## Programming Assistant

```python
import asyncio
from createagents import CreateAgent


async def main():
    code_expert = CreateAgent(
        provider='openai',
        model='gpt-4',
        name='Python Expert',
        instructions='Expert in modern Python, typing, and best practices.',
    )

    code = await code_expert.chat(
        'Create a validated UUID generator with typing annotations.'
    )
    print(code)


asyncio.run(main())
```

## Professional Translator

```python
import asyncio
from createagents import CreateAgent


async def main():
    translator = CreateAgent(
        provider='openai',
        model='gpt-4',
        name='Specialized Translator',
        instructions='You are a professional technical translator.',
    )

    response = await translator.chat(
        "Translate to English: 'A arquitetura clean separa as regras de negócio da infraestrutura.'"
    )
    print(response)


asyncio.run(main())
```

## Data Analyst

```python
import asyncio
from createagents import CreateAgent


async def main():
    analyst = CreateAgent(
        provider='ollama',
        model='llama3.2',
        name='Data Analyst',
        instructions='Provide actionable insights and structured data summaries.',
    )

    data = 'Q1 Sales: Jan=100k, Feb=150k, Mar=120k'
    response = await analyst.chat(f'Analyze these sales figures: {data}')
    print(response)


asyncio.run(main())
```

## Interactive Chatbot (Use the CLI!)

**Recommended**: For interactive chat sessions, launch the **built-in CLI**:

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    name='Friendly Assistant',
)

# Launches interactive CLI
agent.start_cli()
```

The CLI features:

- Formatted colored terminal interface
- Commands: `/help`, `/metrics`, `/configs`, `/tools`, `/clear`
- Real-time streaming support (when initialized with `config={'stream': True}`)
- Status indicators (`🤖 AI is thinking...`)

📖 [Full CLI Guide](cli-usage.md)

### Simple Chat (Custom Loop)

```python
import asyncio
from createagents import CreateAgent


async def main():
    chatbot = CreateAgent(
        provider='openai',
        model='gpt-4',
        name='Simple Chatbot',
        config={'stream': True},
    )

    print("Type 'exit' or 'quit' to end.\n")
    while True:
        user_input = input('You: ')
        if user_input.lower() in ['exit', 'quit']:
            break

        # Streaming
        response = await chatbot.chat(user_input)
        print('Bot: ', end='', flush=True)
        async for token in response:
            print(token, end='', flush=True)
        print('\n')


asyncio.run(main())
```

## Local Agent with Ollama (Processing on localhost)

```python
import asyncio
from createagents import CreateAgent


async def main():
    local_agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        name='Local Assistant',
        instructions='You are a local assistant.',
    )

    response = await local_agent.chat(
        'Explain machine learning in simple terms'
    )
    print(response)


asyncio.run(main())
```

## Real-Time Streaming

```python
import asyncio
from createagents import CreateAgent


async def streaming_example():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        config={'stream': True},
    )

    print('Generating article in real time:\n')
    response = await agent.chat('Write a short summary of Clean Architecture')

    # Stream token by token
    async for token in response:
        print(token, end='', flush=True)
    print('\n\n--- Done ---')


asyncio.run(streaming_example())
```

## Streaming with Ollama

```python
import asyncio
from createagents import CreateAgent


async def ollama_streaming():
    local_agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        name='Local Assistant',
        config={'stream': True},
    )

    response = await local_agent.chat('Explain what an LLM is')
    async for chunk in response:
        print(chunk, end='', flush=True)
    print()


asyncio.run(ollama_streaming())
```

## Next Steps

- [Streaming Guide](streaming-guide.md)
- [CLI Usage](cli-usage.md)
- [FAQ](faq-user.md)
