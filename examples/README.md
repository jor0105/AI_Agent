# Create Agents AI - Examples Directory

Welcome to the **Create Agents AI** examples gallery. This directory contains ready-to-run, standalone examples showcasing all features of the framework—from basic single-turn chats to custom tool creation, streaming, local offline models with Ollama, and full terminal interactive CLIs.

______________________________________________________________________

## ⚡ 2-Minute Quickstart

### 1. Prerequisites & Installation

Ensure you have installed the project dependencies using `uv` (recommended) or `pip`:

```bash
# If developing in this repository:
uv sync --locked

# Or if installing as a standalone package in your project:
pip install createagents
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp examples/.env.example .env
```

Open `.env` and set your credentials:

- **For OpenAI examples**: Set `OPENAI_API_KEY=sk-...`
- **For Ollama examples**: Ensure your Ollama server is running locally (`ollama run llama3.2` or `ollama run mistral`). No API key needed.

### 3. Run Any Example

Run any script directly with Python or `uv run`:

```bash
python examples/01_quickstart_openai.py
# or
uv run python examples/01_quickstart_openai.py
```

______________________________________________________________________

## 📚 Examples Catalog

| #   | Example File                                                         | Description                     | Key Features                                                              |
| --- | -------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------- |
| 01  | [`01_quickstart_openai.py`](01_quickstart_openai.py)                 | Minimal OpenAI assistant        | Cloud inference, basic `CreateAgent` initialization, single-turn chat     |
| 02  | [`02_quickstart_ollama.py`](02_quickstart_ollama.py)                 | Local inference with Ollama     | 100% offline, privacy-first, zero API key required                        |
| 03  | [`03_multi_turn_and_history.py`](03_multi_turn_and_history.py)       | Conversation memory & context   | Multi-turn dialogs, `history_max_size`, inspecting & resetting history    |
| 04  | [`04_streaming_chat.py`](04_streaming_chat.py)                       | Real-time response streaming    | Token-by-token async iteration (`async for chunk in response`)            |
| 05  | [`05_built_in_tools.py`](05_built_in_tools.py)                       | Built-in system tools           | Enabling native tools (`currentdate`), inspecting available catalog       |
| 06  | [`06_custom_tools.py`](06_custom_tools.py)                           | Building custom tools           | Extending `BaseTool`, JSON schema definitions, calculator & weather tools |
| 07  | [`07_interactive_cli.py`](07_interactive_cli.py)                     | Terminal interactive chat       | Full terminal UI with commands (`/help`, `/metrics`, `/tools`, `/clear`)  |
| 08  | [`08_metrics_and_observability.py`](08_metrics_and_observability.py) | Metrics & logging               | Collecting execution metrics, JSON & Prometheus export, log setup         |
| 09  | [`09_specialized_personas.py`](09_specialized_personas.py)           | Persona & hyperparameter tuning | System prompts, `temperature`, `max_tokens`, specialized assistants       |

______________________________________________________________________

## 🛠️ Summary of Common Patterns

### Creating a Cloud Agent (OpenAI)

```python
import asyncio
from createagents import CreateAgent


async def main() -> None:
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        instructions='You are a helpful and concise assistant.',
    )
    response = await agent.chat('What is Clean Architecture in one sentence?')
    print(response)


asyncio.run(main())
```

### Creating a Local Agent (Ollama)

```python
import asyncio
from createagents import CreateAgent


async def main() -> None:
    agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        instructions='You are a helpful local assistant.',
    )
    response = await agent.chat('Hello from my local machine!')
    print(response)


asyncio.run(main())
```

### Streaming Responses in Real Time

```python
import asyncio
from createagents import CreateAgent


async def main() -> None:
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        config={'stream': True},
    )
    response = await agent.chat('Write a 3-line haiku about coding.')
    async for token in response:
        print(token, end='', flush=True)


asyncio.run(main())
```

### Adding a Custom Tool

```python
from createagents import BaseTool, CreateAgent


class SquareTool(BaseTool):
    name = 'square'
    description = 'Calculates the square of a given number.'
    parameters = {
        'type': 'object',
        'properties': {
            'n': {'type': 'number', 'description': 'The number to square'}
        },
        'required': ['n'],
    }

    def execute(self, n: float) -> str:
        return str(n**2)


agent = CreateAgent(
    provider='openai',
    model='gpt-4o-mini',
    tools=[SquareTool()],
)
```
