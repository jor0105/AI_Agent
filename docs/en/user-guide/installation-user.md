# User Installation Guide

> Follow this step-by-step guide to install and configure **Create Agents AI** securely and reliably in your environment.

______________________________________________________________________

## 📝 Prerequisites

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **pip** (usually bundled with Python)

> **Tip:** We recommend using virtual environments to isolate project dependencies.

______________________________________________________________________

## ⚡ Quick Installation

### 1. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

### 2. Install via PyPI

```bash
# Basic installation
pip install createagents

# OR with file support (PDF, Excel, CSV, Parquet)
pip install createagents[file-tools]
```

> **Note:** The `[file-tools]` extra adds support for reading PDF, Excel, CSV, and Parquet files.

The base installation includes `openai`, `ollama`, `python-dotenv`, `defusedxml`, and `rich` — the latter used by the interactive CLI (`start_cli()`).

______________________________________________________________________

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit the .env file and add your OPENAI_API_KEY
```

All recognized environment variables are declared in `.env.example`. Only `OPENAI_API_KEY` is mandatory, and only for the `openai` provider; the others provide sensible defaults and may remain blank:

| Variable                     | Effect                                                | Default                  |
| ---------------------------- | ----------------------------------------------------- | ------------------------ |
| `OPENAI_API_KEY`             | Credential for `openai` provider                      | — (required for OpenAI)  |
| `OPENAI_TIMEOUT`             | Timeout per request in seconds                        | `30`                     |
| `OPENAI_MAX_RETRIES`         | Retries via OpenAI SDK                                | `3`                      |
| `OPENAI_MAX_TOOL_ITERATIONS` | Tool calling rounds per turn                          | `100`                    |
| `OLLAMA_HOST`                | Ollama server URL                                     | `http://localhost:11434` |
| `OLLAMA_MAX_RETRIES`         | Retries per call                                      | `3`                      |
| `OLLAMA_MAX_TOOL_ITERATIONS` | Tool calling rounds per turn                          | `100`                    |
| `LOG_LEVEL`                  | Log level after `LoggingConfig.configure()`           | `INFO`                   |
| `LOG_TO_FILE`                | `true` writes to rotating file                        | `false`                  |
| `LOG_FILE_PATH`              | File destination when `LOG_TO_FILE` is active         | —                        |
| `LOG_JSON_FORMAT`            | `true` emits structured JSON logs                     | `false`                  |
| `FILE_TOOL_BASE_DIR`         | Directory boundary restricted for `ReadLocalFileTool` | Current directory (`.`)  |

______________________________________________________________________

### 4. Test Installation

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='You are a helpful assistant.',
    )
    response = await agent.chat('Hello! Testing installation.')
    print(response)


asyncio.run(main())
```

If the script runs without errors, your installation is complete!

______________________________________________________________________

## 🔑 OpenAI Configuration

1. Create an account at [platform.openai.com](https://platform.openai.com)
2. Generate an API Key under **API Keys**
3. Add it to your `.env` file:

```env
OPENAI_API_KEY=sk-proj-your-key-here
```

> **Warning:** Never commit your API key or publish it in public repositories.

______________________________________________________________________

## 🤖 Ollama Configuration (Optional)

Run models **locally and privately** with zero API costs:

### Install Ollama

**Linux:**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**

```bash
brew install ollama
```

**Windows:**

Download from: [ollama.ai/download/windows](https://ollama.ai/download/windows)

### Pull Models

```bash
ollama pull llama3.2:latest     # Recommended model
ollama pull granite3-dense:latest     # Alternative
ollama list             # View downloaded models
```

### Usage in Code

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        instructions='You are a local assistant.',
    )
    response = await agent.chat('Explain machine learning')
    print(response)


asyncio.run(main())
```

> **Tip:** Run `ollama serve` prior to execution to ensure the local daemon is active.

______________________________________________________________________

## 🔒 Security and Best Practices

- **Never** commit the `.env` file (it is already ignored by `.gitignore`)
- Keep your API keys confidential and rotate them periodically
- Use virtual environments to isolate application dependencies
- Keep dependencies updated (`uv lock --upgrade` or `pip install -U`)

______________________________________________________________________

## 🛠️ Troubleshooting

### Common Errors

- **"OPENAI_API_KEY not found"**: Verify that `.env` is located in the project root and contains no unwanted spaces or enclosing quotes.
- **"ModuleNotFoundError"**: Activate your virtual environment and reinstall packages.
- **Ollama fails to connect**: Ensure `ollama serve` is running and the specified model has been pulled (`ollama list`).
- **Permission errors**: Avoid using `sudo` to install Python packages into the global system interpreter.

### Diagnostic Commands

- Run `uv run python --version` or `python --version` to check active Python version.
- Run `uv tree` or `pip list` to inspect installed dependencies.
- Consult the full error stack trace for details.

If issues persist, consult the [FAQ](faq-user.md) or open an issue on [GitHub](https://github.com/jordanestralioto/Create-Agents-AI/issues).

______________________________________________________________________

## 👨‍💻 Development Installation (Contributors)

If you wish to **contribute** to Create Agents AI or run source builds:

### 1. Clone the Repository

```bash
git clone https://github.com/jordanestralioto/Create-Agents-AI.git
cd Create-Agents-AI
```

### 2. Install with uv

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Base install
uv sync

# OR with file-tools
uv sync --extra file-tools

# Activate virtual environment
source .venv/bin/activate
```

### 3. Configure Development Environment

```bash
cp .env.example .env
# Edit and add your OPENAI_API_KEY
```

### 4. Install Pre-commit Hooks

```bash
# Install code quality hooks
uv sync --locked
uv run --locked --no-sync pre-commit install --install-hooks

# Run all checks manually
uv run --locked --no-sync pre-commit run --all-files
```

📖 **More info:** [Contribution Guide](../dev-guide/contribute.md)

______________________________________________________________________

## 🚀 Next Steps

- [Basic Usage](basic-usage-user.md)
- [Examples](examples-user.md)
- [FAQ](faq-user.md)
- [Tools Reference](../reference/tools.md)
- [API Reference](../reference/api.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
