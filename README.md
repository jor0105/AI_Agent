# Create Agents AI

<div align="center">

**Production-oriented Python library for building conversational AI agents with pluggable providers, extensible tools, conversation history, and metrics following Clean Architecture.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/createagents.svg)](https://pypi.org/project/createagents/)
[![CI Pipeline](https://github.com/jordanestralioto/Create-Agents-AI/actions/workflows/pipeline.yml/badge.svg)](https://github.com/jordanestralioto/Create-Agents-AI/actions/workflows/pipeline.yml)
[![codecov](https://codecov.io/gh/jordanestralioto/Create-Agents-AI/graph/badge.svg)](https://codecov.io/gh/jordanestralioto/Create-Agents-AI)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-Ruff-D7FF64.svg)](https://docs.astral.sh/ruff/)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)

[Documentation](docs/en/index.md) • [Quick Start](#quick-start) • [API Reference](docs/en/reference/api.md) • [Contributing](CONTRIBUTING.md) • [Security](SECURITY.md) • [License](LICENSE)

</div>

______________________________________________________________________

## Overview

**Create Agents AI** (`createagents`) is a modular and extensible Python framework designed to build intelligent, testable conversational agents. Built on **Clean Architecture** and **SOLID** principles, it provides strict provider isolation, automatic conversation history, tool integration, metrics export, and an interactive terminal CLI.

> **Project status:** Beta. APIs and behavior may evolve as the project matures.

### Key Capabilities

- **Clean Architecture**: Inward dependency flow with business logic isolated from external frameworks and providers.
- **Pluggable Providers**: First-class support for OpenAI and Ollama (local and private on localhost).
- **Extensible Tools**: Standard `BaseTool` interface with built-in date/time and secure local file reading.
- **Contextual History**: Automatic multi-turn conversation memory management.
- **Metrics Export**: Export interaction metrics to JSON and Prometheus formats without requiring external daemons.
- **Silent by Default**: Zero unsolicited console logging until explicitly enabled via `LoggingConfig`.
- **Type Safety & Quality**: The codebase is type-checked with mypy, verified with Ruff and Bandit, and covered by automated test gates.

### Supported Providers

| Provider   | Status    | Prerequisites                                                |
| ---------- | --------- | ------------------------------------------------------------ |
| **OpenAI** | Supported | `OPENAI_API_KEY` environment variable                        |
| **Ollama** | Supported | Reachable Ollama instance (no API key required on localhost) |

______________________________________________________________________

## Installation

### For End Users

Install the latest published package from PyPI:

```bash
# Standard installation
pip install createagents

# With file-reading tools (PDF, Excel, CSV, Parquet)
pip install 'createagents[file-tools]'
```

### For Development and Contributors

Clone the repository and use [uv](https://docs.astral.sh/uv/) for reproducible dependency resolution:

```bash
git clone https://github.com/jordanestralioto/Create-Agents-AI.git
cd Create-Agents-AI

# Install all locked dependencies
uv sync --locked

# Or include optional file-tools
uv sync --locked --extra file-tools
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Developer Contribution Guide](docs/en/dev-guide/contribute.md) for full instructions.

______________________________________________________________________

## Quick Start

### 1. OpenAI Agent

Set your API key:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

> **Note**: Replace `"YOUR_MODEL"` below with your desired OpenAI model identifier.

```python
import asyncio
from createagents import CreateAgent


async def main() -> None:
    # Initialize the agent
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        instructions='You are a helpful and concise software engineering assistant.',
    )

    # Send a message
    response = await agent.chat('How do I structure a Python project?')
    print(response)


if __name__ == '__main__':
    asyncio.run(main())
```

### 2. Local Ollama Agent

Ensure your Ollama server is running and pull your preferred model:

```bash
# Pull model and start the Ollama server
ollama pull YOUR_OLLAMA_MODEL
ollama serve
```

> **Note**: Replace `"YOUR_OLLAMA_MODEL"` with a locally installed model name.

```python
import asyncio
from createagents import CreateAgent


async def main() -> None:
    # Initialize local Ollama agent
    agent = CreateAgent(
        provider='ollama',
        model='YOUR_OLLAMA_MODEL',
        instructions='You are a local private assistant.',
    )

    response = await agent.chat('Explain Clean Architecture in two sentences.')
    print(response)


if __name__ == '__main__':
    asyncio.run(main())
```

______________________________________________________________________

## Built-in Tools

Create Agents AI includes standard tools out of the box and supports custom extensions through `BaseTool`.

| Tool Name       | Class               | Description                                                                                                            | Requirements                             |
| --------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `currentdate`   | `CurrentDateTool`   | Current date/time across any IANA timezone                                                                             | Built-in                                 |
| `readlocalfile` | `ReadLocalFileTool` | Reads local text, markdown, CSV, Excel (`.xlsx`, `.xlsm`, and `.xls` subject to reader availability), PDF, and Parquet | `pip install 'createagents[file-tools]'` |

### Using Tools

```python
import asyncio
from createagents import CreateAgent


async def main() -> None:
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        tools=['currentdate'],
    )

    # The agent automatically determines when to call the tool
    response = await agent.chat(
        'What is the current time in America/New_York?'
    )
    print(response)


if __name__ == '__main__':
    asyncio.run(main())
```

______________________________________________________________________

## Configuration & Environment

### Environment Variables

| Variable                     | Scope     | Purpose                                                    |
| ---------------------------- | --------- | ---------------------------------------------------------- |
| `OPENAI_API_KEY`             | OpenAI    | Required API authentication token                          |
| `OPENAI_TIMEOUT`             | OpenAI    | Request timeout in seconds                                 |
| `OPENAI_MAX_RETRIES`         | OpenAI    | Maximum retry attempts for failed requests                 |
| `OPENAI_MAX_TOOL_ITERATIONS` | OpenAI    | Maximum tool execution loops per chat turn                 |
| `OLLAMA_HOST`                | Ollama    | Ollama server host URL (default: `http://localhost:11434`) |
| `OLLAMA_MAX_RETRIES`         | Ollama    | Maximum retry attempts for Ollama requests                 |
| `OLLAMA_MAX_TOOL_ITERATIONS` | Ollama    | Maximum tool execution loops per chat turn                 |
| `LOG_LEVEL`                  | Logging   | Base logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)   |
| `LOG_TO_FILE`                | Logging   | Enable writing logs to disk (`true`/`false`)               |
| `LOG_FILE_PATH`              | Logging   | Destination path for log files                             |
| `LOG_JSON_FORMAT`            | Logging   | Format logs as structured JSON (`true`/`false`)            |
| `FILE_TOOL_BASE_DIR`         | File Tool | Restricts `readlocalfile` access to a sandbox directory    |

### Agent Runtime Configuration

```python
from createagents import CreateAgent

config = {
    'temperature': 0.7,  # Allowed range: 0.0 to 2.0
    'max_tokens': 1500,  # Positive integer
    'top_p': 0.9,  # Allowed range: 0.0 to 1.0
    'stream': False,  # Enable token-by-token streaming
}

# Provider-specific reasoning/thinking options:
# Ollama: think=True/False or "low"|"medium"|"high"
# OpenAI: think="low"|"medium"|"high" (on supported reasoning models)

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='Be technical and concise.',
    config=config,
    history_max_size=20,
)
```

______________________________________________________________________

## Logging & Metrics

### Silent Library Logging

The library installs a `NullHandler` and remains completely silent by default. Consumers can opt into logging during development or configure handlers explicitly:

```python
import logging
from createagents import LoggingConfig

# Enable console logging for development
LoggingConfig.configure_for_development(level=logging.INFO)
```

### Metrics Export

Collect and export interaction metrics (latency, token counts, model calls) to structured JSON or Prometheus format strings and files:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')

# Retrieve metrics objects
metrics = agent.get_metrics()

# Export metrics to JSON or Prometheus format files/strings
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

> **Note**: The package exports metrics formatted for Prometheus scraping or file collectors; it does not run a background Prometheus HTTP server or monitoring daemon.

______________________________________________________________________

## Architecture

Create Agents AI is structured around strict Clean Architecture boundaries:

```
┌────────────────────────────────────────────────────────────┐
│ MAIN (Composition Root & Facade)                           │
│ CreateAgent: src/createagents/main/facade/client.py        │
│ AgentComposer: src/createagents/main/composers/            │
└──────────────────────────────┬─────────────────────────────┘
                               │ wires and injects dependencies
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐   ┌────────────────┐   ┌────────────────────────┐
│ PRESENTATION  │   │ APPLICATION    │   │ INFRASTRUCTURE         │
│ CLI Terminal  │──▶│ Use Cases      │◀──│ Adapters & Factories   │
│ Application   │   │ DTOs & Ports   │   │ (OpenAI, Ollama, Tools)│
└───────────────┘   └───────┬────────┘   └────────────────────────┘
                            │ depends only on
                            ▼
                    ┌────────────────┐
                    │ DOMAIN         │
                    │ Entities/Rules │
                    └────────────────┘
```

- **Domain**: Pure business entities, value objects, and domain exceptions. No external dependencies.
- **Application**: Use cases, DTOs, and interface ports (e.g. `ChatRepository`). Depends solely on Domain.
- **Infrastructure**: Concrete adapters implementing application ports (OpenAI, Ollama, tools, logging, metrics).
- **Presentation**: Interactive terminal CLI consuming the application facade lazily.
- **Main**: Composition root (`AgentComposer`) wiring concrete adapters into use cases, and the public `CreateAgent` facade.

Read the [Architecture Developer Guide](docs/en/dev-guide/architecture-developer.md) for full architectural details.

______________________________________________________________________

## Documentation Directory

The complete documentation suite is published and accessible:

### English Documentation (Primary)

- **User Guide**: [Installation](docs/en/user-guide/installation-user.md) • [Basic Usage](docs/en/user-guide/basic-usage-user.md) • [CLI Usage](docs/en/user-guide/cli-usage.md) • [Streaming Guide](docs/en/user-guide/streaming-guide.md) • [Examples](docs/en/user-guide/examples-user.md) • [FAQ](docs/en/user-guide/faq-user.md)
- **Developer Guide**: [Architecture](docs/en/dev-guide/architecture-developer.md) • [CLI Architecture](docs/en/dev-guide/cli-architecture.md) • [Async Guide](docs/en/dev-guide/async-guide.md) • [Logging Guide](docs/en/dev-guide/logging_guide.md) • [Technical Examples](docs/en/dev-guide/technical-examples.md) • [How to Contribute](docs/en/dev-guide/contribute.md)
- **Reference**: [API Reference](docs/en/reference/api.md) • [Streaming API](docs/en/reference/streaming-api.md) • [Metrics API](docs/en/reference/metrics-api.md) • [Tools](docs/en/reference/tools.md) • [CLI Commands](docs/en/reference/commands.md)

### Portuguese Documentation

- [Portuguese Documentation Home](docs/index.md)

______________________________________________________________________

## Governance & Community

- **Contributing**: Please review [CONTRIBUTING.md](CONTRIBUTING.md) and the [Contribution Guide](docs/en/dev-guide/contribute.md).
- **Security**: For vulnerability reporting, please see [SECURITY.md](SECURITY.md).
- **Code of Conduct**: Community standards are defined in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- **License**: Released under the [MIT License](LICENSE).

## Support & Contact

- **Maintainer**: Jordan Estralioto
- **Email**: `estraliotojordan@gmail.com`
- **Security**: Please report security vulnerabilities privately according to [SECURITY.md](SECURITY.md).
