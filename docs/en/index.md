# 🤖 Create Agents AI

> Production-oriented Python framework for building intelligent AI agents with Clean Architecture, multiple providers, and extensible tools.

> **Project status:** Beta. APIs and behavior may evolve as the project matures.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-brightgreen.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

______________________________________________________________________

## 🎯 What Does This Framework Offer?

**Create Agents AI** is a Python framework that enables building professional conversational AI agents:

- ✅ **Multiple Providers**: OpenAI and Ollama (local) with seamless switching
- ✅ **Extensible Tools**: CurrentDateTool and ReadLocalFileTool (PDF, Excel, CSV, and Parquet)
- ✅ **Automatic History**: Contextual multi-turn conversations effortlessly
- ✅ **Built-in Metrics**: Monitor performance via JSON or Prometheus formats
- ✅ **Clean Architecture**: Testable, maintainable, and scalable codebase adhering to SOLID principles

______________________________________________________________________

## 🚀 Quick Start

### Installation

```bash
# Basic installation via PyPI
pip install createagents

# OR with file-reading capabilities (PDF, Excel, CSV, Parquet)
pip install 'createagents[file-tools]'
```

### Configuration

**PyPI Installation:**

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-proj-your-api-key-here
```

*(If working from a repository clone, copy the template with `cp .env.example .env`).*

> **Note:** OpenAI requires `OPENAI_API_KEY`. Ollama requires no API key when running on `localhost` (refer to the [installation guide](user-guide/installation-user.md) for details). Replace `"YOUR_MODEL"` with your desired OpenAI model and `"YOUR_OLLAMA_MODEL"` with a locally installed Ollama model.

### First Agent in 3 Lines

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        instructions='You are a helpful assistant',
    )

    response = await agent.chat('Hello!')
    print(response)


asyncio.run(main())
```

______________________________________________________________________

## ✨ Key Features

### 🤝 Multiple Providers

```python
from createagents import CreateAgent

# OpenAI
agent_openai = CreateAgent(provider='openai', model='YOUR_MODEL')

# Ollama (local processing on localhost)
agent_local = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
```

### 🔧 Built-in Tools

Empower your agents with ready-to-use tools:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        tools=['currentdate'],  # 'readlocalfile' requires [file-tools]
    )

    # The agent automatically invokes tools when necessary
    response = await agent.chat('What day is today?')  # Uses CurrentDateTool
    print(response)

    # Check available tools
    all_tools = agent.get_all_available_tools()
    print(f'Total tools: {len(all_tools)}')

    # View only system-provided tools
    system_tools = agent.get_system_available_tools()
    for name in system_tools.keys():
        print(f'  • {name}')


asyncio.run(main())
```

**Available Tools:**

- `currentdate` - Current date/time in any timezone (always available)
- `readlocalfile` - Reads PDF, Excel, CSV, Parquet, JSON, YAML, TXT (requires `pip install 'createagents[file-tools]'`)

**Creating Custom Tools:**

```python
from createagents import BaseTool, CreateAgent


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


# Use custom tool alongside built-ins
agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    tools=['currentdate', WordCountTool()],
)

# Inspect all available tools
print(agent.get_all_available_tools().keys())
```

### 💬 Contextual History

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')

    await agent.chat('Hello!')
    await agent.chat('What is the capital of France?')  # Keeps context
    await agent.chat('And what is its population?')  # Uses previous context

    # View history
    config = agent.get_configs()
    print(f'History: {len(config["history"])} messages')

    # Clear history when needed
    agent.clear_history()


asyncio.run(main())
```

### 📊 Metrics Export

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')

# Retrieve metrics
metrics = agent.get_metrics()

# Export in different formats (JSON or Prometheus format)
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

### ⚙️ Custom Configuration

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='Be concise and technical',
    config={
        'temperature': 0.7,  # Allowed range: 0.0 to 2.0
        'max_tokens': 2000,  # Response limit
    },
    history_max_size=20,  # History size limit
)
```

______________________________________________________________________

## 📚 Documentation

### For Users

- **[Installation](user-guide/installation-user.md)** - Step-by-step environment setup
- **[Basic Usage](user-guide/basic-usage-user.md)** - Learn the fundamentals
- **[CLI Usage](user-guide/cli-usage.md)** - Interactive terminal interface
- **[Streaming Guide](user-guide/streaming-guide.md)** - Real-time responses and async streaming
- **[Practical Examples](user-guide/examples-user.md)** - Real-world use cases
- **[FAQ](user-guide/faq-user.md)** - Frequently Asked Questions

### For Developers

- **[Architecture](dev-guide/architecture-developer.md)** - Clean Architecture and design patterns
- **[Technical Examples](dev-guide/technical-examples.md)** - Advanced patterns
- **[How to Contribute](dev-guide/contribute.md)** - Contribution guidelines

### Reference

- **[API Reference](reference/api.md)** - Complete API documentation
- **[Tools](reference/tools.md)** - Guide to all available tools
- **[Commands](reference/commands.md)** - Interactive CLI commands reference

______________________________________________________________________

## 🏗️ Why Use This Framework?

### For Organizations

- ✅ **Privacy**: Option for local models on localhost with Ollama (zero API costs and local data retention when `OLLAMA_HOST` is not pointed to an external server)
- ✅ **Security**: Automatic sanitization of sensitive data in logs
- ✅ **Metrics Export**: Structured metrics export in JSON and Prometheus formats
- ✅ **Scalability**: Architecture designed for extensibility

### For Developers

- ✅ **Clean Architecture**: Clean, testable, and maintainable codebase
- ✅ **SOLID**: Easy to extend with new providers and tools
- ✅ **Type Hints**: Full IDE autocompletion support
- ✅ **CI/CD**: Automated quality checks with GitHub Actions

______________________________________________________________________

## 📊 Architecture

The project strictly adheres to **Clean Architecture** and **SOLID principles**:

```
┌────────────────────────────────────────────────────────────┐
│ MAIN                                                        │
│ CreateAgent: src/createagents/main/facade/client.py        │
│ AgentComposer (composition root)                           │
└──────────────────────────────┬─────────────────────────────┘
                               │ composes and injects dependencies
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐   ┌────────────────┐   ┌────────────────────────┐
│ PRESENTATION  │   │ APPLICATION    │   │ INFRASTRUCTURE         │
│ CLI           │──▶│ Use Cases      │◀──│ Adapters / Factories    │
└───────────────┘   └───────┬────────┘   └────────────────────────┘
                            │ depends on
                            ▼
                    ┌────────────────┐
                    │ DOMAIN         │
                    │ Entities/Rules │
                    └────────────────┘
```

**Benefits**: Testable, Flexible, Scalable, and Maintainable

`CreateAgent` does not belong to the Presentation layer: the public facade lives in `src/createagents/main/facade/`, while the CLI lives in `src/createagents/presentation/cli/`. The composition root is `src/createagents/main/composers/agent_composer.py`. The application layer depends solely on domain; infrastructure and presentation implement the ports consumed by use cases.

[Learn more about the architecture →](dev-guide/architecture-developer.md)

______________________________________________________________________

## 🤝 Contributing

Looking to add a new provider or build a custom tool?

1. Read the [contribution guide](dev-guide/contribute.md).

2. Fork the repository and create a branch: `git checkout -b feature/add-provider`

3. Implement following established architectural patterns.

4. Run safe local tests:

   ```bash
   uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov
   ```

5. Verify remaining quality gates described in the guide.

6. Submit a Pull Request.

[Full contribution guide →](dev-guide/contribute.md)

______________________________________________________________________

## 📞 Support

- 📧 **Email**: `estraliotojordan@gmail.com`
- 🔒 **Security**: Please report security vulnerabilities privately according to our [Security Policy](https://github.com/jordanestralioto/Create-Agents-AI/blob/develop/SECURITY.md).

______________________________________________________________________

## 📄 License

MIT - Free for use in commercial and open-source projects.

______________________________________________________________________

## 👨‍💻 Author

**Jordan Estralioto**

- GitHub: [@jordanestralioto](https://github.com/jordanestralioto)
- Email: estraliotojordan@gmail.com

______________________________________________________________________

**Version:** 0.2.0\
**Last updated:** 2026-08-27\
**Status:** 🚀 Published package! Open for contributions and feedback.
