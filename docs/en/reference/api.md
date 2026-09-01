# 📚 API Reference

Complete documentation for the public API of **Create Agents AI**.

______________________________________________________________________

## 🤖 `CreateAgent`

Main client facade for creating and interacting with AI agents.

### Constructor

```python
def __init__(
    self,
    provider: str,
    model: str,
    name: str | None = None,
    instructions: str | None = None,
    config: Dict[str, Any] | None = None,
    tools: Sequence[Union[str, BaseTool]] | None = None,
    history_max_size: int = 10,
) -> None: ...
```

**Parameters:**

| Parameter          | Type   | Description                                                                       | Required |
| ------------------ | ------ | --------------------------------------------------------------------------------- | -------- |
| `provider`         | `str`  | AI provider: `"openai"` or `"ollama"`                                             | ✅ Yes   |
| `model`            | `str`  | Model identifier (e.g. `"YOUR_MODEL"`, `"YOUR_OLLAMA_MODEL"`)                     | ✅ Yes   |
| `name`             | `str`  | Agent display name                                                                | ❌ No    |
| `instructions`     | `str`  | System prompt / instructions                                                      | ❌ No    |
| `config`           | `dict` | Model hyperparameters (`temperature`, `max_tokens`, `stream`, etc.)               | ❌ No    |
| `tools`            | `list` | List of tools (e.g. `["currentdate"]`; `"readlocalfile"` requires `[file-tools]`) | ❌ No    |
| `history_max_size` | `int`  | Maximum messages preserved in history (default: 10)                               | ❌ No    |

**Example:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='You are a technical assistant',
    config={'temperature': 0.7, 'max_tokens': 2000},
    tools=['currentdate'],
    history_max_size=20,
)
```

______________________________________________________________________

### Methods

#### `chat()`

Sends a message to the agent and receives a response.

```python
async def chat(message: str) -> Union[str, StreamingResponseDTO]: ...
```

**Parameters:**

- `message` (`str`): User message text

**Returns:** `Union[str, StreamingResponseDTO]` - Complete string or streaming wrapper depending on `stream` config.

**Example:**

```python
import asyncio


async def main():
    response = await agent.chat('How do I create a class in Python?')
    print(response)


asyncio.run(main())
```

______________________________________________________________________

#### `get_configs()`

Returns current configuration dictionary and conversation history.

```python
def get_configs() -> Dict[str, Any]: ...
```

**Returns:** `dict` containing:

- `name`: Agent name
- `model`: Model name
- `provider`: Provider (`openai` or `ollama`)
- `instructions`: System prompt
- `history`: List of message dictionaries
- `history_max_size`: History limit
- `tools`: List of configured tool names active on this agent
- `config`: Additional configuration parameters

______________________________________________________________________

#### `clear_history()`

Clears conversation history.

```python
def clear_history() -> None: ...
```

______________________________________________________________________

#### `get_all_available_tools()`

Returns the discovery catalog of all tools available in the environment for this agent (system built-in tools + custom registered tools).

> **Note:** To view which tools are **active on this specific agent** for chat interactions, inspect `agent.get_configs()['tools']`.

```python
def get_all_available_tools() -> Dict[str, str]: ...
```

**Returns:** `dict` mapping tool names to descriptions.

**Behavior:**

- Includes all built-in framework tools available in the environment
- Includes custom tools registered when the agent was instantiated
- Deduplicates tools automatically if a built-in tool is explicitly added

**Example:**

```python
from createagents import BaseTool, CreateAgent


# Custom tool definition
class MyTool(BaseTool):
    name = 'my_tool'
    description = 'My custom tool'
    parameters = {
        'type': 'object',
        'properties': {
            'input': {
                'type': 'string',
                'description': 'Input query for the tool',
            },
            'limit': {
                'type': 'integer',
                'description': '(Optional) Max items to return',
            },
        },
        'required': ['input'],
    }

    def execute(self, **kwargs) -> str:
        input_val = kwargs.get('input', '')
        limit = kwargs.get('limit', None)
        return f'Result for: {input_val}' + (
            f' (limit={limit})' if limit is not None else ''
        )


# Instantiate agent with custom tool
agent = CreateAgent(
    provider='openai', model='YOUR_MODEL', tools=['currentdate', MyTool()]
)

# List all available tools
tools = agent.get_all_available_tools()
for name, description in tools.items():
    print(f'- {name}: {description}')
```

______________________________________________________________________

#### `get_system_available_tools()`

Returns only the built-in system tools available globally across the framework.

```python
def get_system_available_tools() -> Dict[str, str]: ...
```

**Returns:** `dict` mapping system tool names to descriptions.

**Behavior:**

- Returns only framework built-in tools
- Does not include agent-specific custom tools
- Useful for checking whether optional tools (like `ReadLocalFileTool`) are installed

**Example:**

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')

system_tools = agent.get_system_available_tools()
print('System tools available:')
for name, description in system_tools.items():
    print(f'- {name}: {description[:50]}...')

# Check if optional file tool is available
if 'readlocalfile' in system_tools:
    print('✅ ReadLocalFileTool is available')
else:
    print("❌ Install with: pip install 'createagents[file-tools]'")
```

**Comparison:**

| Method                         | System Tools | Custom Tools | Use Case                                 |
| ------------------------------ | ------------ | ------------ | ---------------------------------------- |
| `get_all_available_tools()`    | ✅ Yes       | ✅ Yes       | Inspect full available tool catalog      |
| `get_system_available_tools()` | ✅ Yes       | ❌ No        | Check which built-in tools are installed |

______________________________________________________________________

#### `get_metrics()`

Returns interaction metrics.

```python
def get_metrics() -> List[ChatMetrics]: ...
```

**Returns:** `List[ChatMetrics]` objects with:

- `latency_ms` (`float`): Latency in milliseconds
- `tokens_used` (`int | None`): Total tokens consumed
- `success` (`bool`): Success status
- `timestamp` (`datetime`): Execution timestamp

______________________________________________________________________

#### `export_metrics_json()`

Exports collected metrics to JSON.

```python
def export_metrics_json(filepath: str | None = None) -> str: ...
```

______________________________________________________________________

#### `export_metrics_prometheus()`

Exports collected metrics in Prometheus format.

```python
def export_metrics_prometheus(filepath: str | None = None) -> str: ...
```

______________________________________________________________________

#### `start_cli()`

Launches an interactive terminal chat session.

```python
def start_cli() -> None: ...
```

**Description:**

Launches a terminal CLI interface featuring:

- Formatted ANSI boxed UI
- Interactive commands: `/help`, `/metrics`, `/configs`, `/tools`, `/clear`
- Real-time streaming support (when initialized with `config={'stream': True}`)
- Status indicator (`🤖 AI is thinking...`)

**Example:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    config={'stream': True},
)
agent.start_cli()  # Launches interactive CLI with streaming
```

> 📚 [Full CLI Guide](../user-guide/cli-usage.md)

______________________________________________________________________

## 🛠️ Tools

### Available Built-in Tools

#### `CurrentDateTool`

Provides current date and time in any timezone.

**Name:** `"currentdate"`

**Usage:**

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

**Actions:**

- `date`: Date (YYYY-MM-DD)
- `time`: Time (HH:MM:SS)
- `datetime`: Full date and time
- `timestamp`: Unix timestamp
- `date_with_weekday`: Formatted date with day of the week

______________________________________________________________________

#### `ReadLocalFileTool`

Reads local files across 32 formats with a strict 100 MiB (104,857,600 bytes) security ceiling.

**Name:** `"readlocalfile"`

**Requires:** `pip install 'createagents[file-tools]'`

**Supported Formats (32 extensions):**

- **Text & Source Code:** TXT, LOG, MD, PY, JS, HTML, CSS, JSON, XML, YAML, YML, RST, INI, CFG, CONF, SH, BASH, ZSH
- **Tables & Data:** CSV, Excel (XLSX, XLSM, and legacy XLS with `xlrd`), Parquet
- **Documents:** PDF, Word (DOC, DOCX), PowerPoint (PPT, PPTX), OpenDocument (ODT), EPUB, MSG, RTF

**Usage:**

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', tools=['readlocalfile']
    )

    response = await agent.chat('Summarize document.pdf')
    print(response)


asyncio.run(main())
```

**Limits:**

- Maximum file size: 100 MiB (104,857,600 bytes)
- Maximum tokens: Depends on the configured model's context window

______________________________________________________________________

## 📊 Model Configuration Parameters

Parameters to control model behavior (OpenAI/Ollama):

```python
from createagents import CreateAgent

config = {
    'temperature': 0.7,  # 0.0–2.0: Creativity
    'max_tokens': 2000,  # >0: Completion limit
    'top_p': 0.9,  # 0.0–1.0: Nucleus sampling
    'think': 'medium',  # OpenAI: "low"|"medium"|"high"; Ollama: bool or "low"|"medium"|"high"
    'top_k': 40,  # >0: (Ollama)
}

agent = CreateAgent(provider='openai', model='YOUR_MODEL', config=config)
```

**Supported Parameters:**

| Name          | Range / Type    | Description                                                                                          |
| ------------- | --------------- | ---------------------------------------------------------------------------------------------------- |
| `temperature` | `0.0` – `2.0`   | Sampling randomness; model-dependent for OpenAI (GPT-5, GPT-5 Mini, and GPT-5 nano do not accept it) |
| `max_tokens`  | `>0` (`int`)    | Maximum completion tokens                                                                            |
| `top_p`       | `0.0` – `1.0`   | Nucleus sampling; model-dependent for OpenAI (GPT-5, GPT-5 Mini, and GPT-5 nano do not accept it)    |
| `think`       | `bool` or `str` | Extended reasoning (Ollama: `bool`; OpenAI: `"low"`, `"medium"`, `"high"`)                           |
| `top_k`       | `>0` (`int`)    | Top-k sampling limit (Ollama)                                                                        |
| `stream`      | `bool`          | Enables real-time streaming (`StreamingResponseDTO`)                                                 |

______________________________________________________________________

## 💡 Usage Examples

### Basic Example

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    response = await agent.chat('Hello!')
    print(response)


asyncio.run(main())
```

### With Tools

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        tools=['currentdate'],  # add 'readlocalfile' with the file-tools extra
    )

    response = await agent.chat('What day is today?')
    print(response)


asyncio.run(main())
```

### Local (Ollama)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
    response = await agent.chat('Explain AI')
    print(response)


asyncio.run(main())
```

### Interactive CLI

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
agent.start_cli()  # Full terminal interface
```

______________________________________________________________________

**Version:** 0.3.0 | **Updated:** 2026-08-27
