# 📚 API Reference

Complete documentation for the public API of **Create Agents AI**.

______________________________________________________________________

## 🤖 `CreateAgent`

Main client facade for creating and interacting with AI agents.

### Constructor

```python
CreateAgent(
    provider: str,
    model: str,
    name: Optional[str] = None,
    instructions: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    tools: Optional[Sequence[Union[str, BaseTool]]] = None,
    history_max_size: int = 10,
)
```

**Parameters:**

| Parameter          | Type   | Description                                                         | Required |
| ------------------ | ------ | ------------------------------------------------------------------- | -------- |
| `provider`         | `str`  | AI provider: `"openai"` or `"ollama"`                               | ✅ Yes   |
| `model`            | `str`  | Model identifier (e.g. `"gpt-4o-mini"`, `"llama3.2"`)               | ✅ Yes   |
| `name`             | `str`  | Agent display name                                                  | ❌ No    |
| `instructions`     | `str`  | System prompt / instructions                                        | ❌ No    |
| `config`           | `dict` | Model hyperparameters (`temperature`, `max_tokens`, `stream`, etc.) | ❌ No    |
| `tools`            | `list` | List of tool names or `BaseTool` instances                          | ❌ No    |
| `history_max_size` | `int`  | Maximum messages preserved in history (default: 10)                 | ❌ No    |

**Example:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='gpt-4o-mini',
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
async def chat(message: str) -> Union[str, StreamingResponseDTO]
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
def get_configs() -> Dict[str, Any]
```

**Returns:** `dict` containing:

- `name`: Agent name
- `model`: Model name
- `provider`: Provider (`openai` or `ollama`)
- `instructions`: System prompt
- `history`: List of message dictionaries
- `history_max_size`: History limit
- `tools`: List of configured tool names
- `config`: Additional configuration parameters

______________________________________________________________________

#### `clear_history()`

Clears conversation history.

```python
def clear_history() -> None
```

______________________________________________________________________

#### `get_all_available_tools()`

Returns all tools available for this specific agent (system built-in tools + custom tools).

```python
def get_all_available_tools() -> Dict[str, str]
```

**Returns:** `dict` mapping tool names to descriptions.

______________________________________________________________________

#### `get_system_available_tools()`

Returns only the built-in system tools available globally.

```python
def get_system_available_tools() -> Dict[str, str]
```

**Comparison:**

| Method                         | System Tools | Custom Tools | Use Case                                 |
| ------------------------------ | ------------ | ------------ | ---------------------------------------- |
| `get_all_available_tools()`    | ✅ Yes       | ✅ Yes       | Inspect all tools this agent can use     |
| `get_system_available_tools()` | ✅ Yes       | ❌ No        | Check which built-in tools are installed |

______________________________________________________________________

#### `get_metrics()`

Returns interaction metrics.

```python
def get_metrics() -> List[ChatMetrics]
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
def export_metrics_json(filepath: Optional[str] = None) -> str
```

______________________________________________________________________

#### `export_metrics_prometheus()`

Exports collected metrics in Prometheus format.

```python
def export_metrics_prometheus(filepath: Optional[str] = None) -> str
```

______________________________________________________________________

#### `start_cli()`

Launches an interactive terminal chat session.

```python
def start_cli() -> None
```

______________________________________________________________________

## 🛠️ Tools

### `CurrentDateTool`

Provides current date and time in any timezone.

- **Name:** `"currentdate"`
- **Actions:** `date`, `time`, `datetime`, `timestamp`, `date_with_weekday`

### `ReadLocalFileTool`

Reads local files across text, PDF, Excel, CSV, and Parquet formats.

- **Name:** `"readlocalfile"`
- **Requires:** `pip install createagents[file-tools]`
- **Security:** Path traversal sandbox controlled by `FILE_TOOL_BASE_DIR`

______________________________________________________________________

## 📊 Model Configuration Parameters

| Name          | Range / Type    | Description                                                                |
| ------------- | --------------- | -------------------------------------------------------------------------- |
| `temperature` | `0.0` – `2.0`   | Sampling randomness (0 = deterministic, 2 = creative)                      |
| `max_tokens`  | `>0` (`int`)    | Maximum completion tokens                                                  |
| `top_p`       | `0.0` – `1.0`   | Nucleus sampling probability                                               |
| `think`       | `bool` or `str` | Extended reasoning (Ollama: `bool`; OpenAI: `"low"`, `"medium"`, `"high"`) |
| `top_k`       | `>0` (`int`)    | Top-k sampling limit (Ollama)                                              |
| `stream`      | `bool`          | Enables real-time streaming (`StreamingResponseDTO`)                       |

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
