# 📝 Logging Guide

This guide explains how to configure and utilize the logging system in `CreateAgentsAI`, which follows **Clean Architecture** with domain logging abstractions and infrastructure implementations.

______________________________________________________________________

## 🏗️ Logging Architecture

### `LoggerInterface` (Domain)

The library defines an abstract **`LoggerInterface`** in the domain layer (`src/createagents/domain/interfaces/`), allowing domain and application layers to log without depending on concrete infrastructure details.

```python
from abc import ABC, abstractmethod


class LoggerInterface(ABC):
    """Abstract logging interface."""

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> None:
        pass
```

### `StandardLogger` (Infrastructure)

The concrete implementation lives in the infrastructure layer (`src/createagents/infra/config/`):

```python
class StandardLogger(LoggerInterface):
    """Standard implementation of LoggerInterface using Python logging."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(message, *args, **kwargs)

    # ...other methods
```

______________________________________________________________________

## 🔇 Default Behavior (Silent by Default)

When importing and using Create Agents AI, no log output is emitted to console or file unless you explicitly configure the logging system.

This is done intentionally to avoid conflicting with the host application's logging configuration.

______________________________________________________________________

## 🛠️ How to Enable Logging

### Option 1: Quick Development Setup

For development, testing, or simple scripts, use `configure_for_development`:

```python
import logging
from createagents import LoggingConfig

# Enable INFO level logs
LoggingConfig.configure_for_development(level=logging.INFO)

# Or for full trace (DEBUG)
LoggingConfig.configure_for_development(level=logging.DEBUG)
```

This configures readable console output (via `StreamHandler`) and automatic sensitive data sanitization.

### Option 2: Standard Python Logging

If your application already configures root logging, the library will integrate smoothly:

```python
import logging

# Host application logging configuration
logging.basicConfig(level=logging.INFO)

# Library logs will now appear
from createagents import CreateAgent
```

### Option 3: Targeted Configuration for `'createagents'`

To control logging specifically for the framework:

```python
import logging

# Configure only the 'createagents' logger
logger = logging.getLogger('createagents')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
```

______________________________________________________________________

## 🎯 Usage in Custom Components

When extending the library (e.g. creating custom tools or handlers), you can inject `LoggerInterface`:

### Example: Custom Tool with Logging

```python
from createagents import BaseTool
from createagents.domain.interfaces import LoggerInterface


class MyCustomTool(BaseTool):
    name = 'my_tool'
    description = 'My custom tool'
    parameters = {...}

    def __init__(self, logger: LoggerInterface):
        self._logger = logger

    def execute(self, **kwargs) -> str:
        self._logger.info('Executing MyCustomTool with: %s', kwargs)
        try:
            result = self._do_something(kwargs)
            self._logger.debug('Result: %s', result)
            return result
        except Exception as e:
            self._logger.error('Error in MyCustomTool: %s', str(e))
            raise
```

### Dependency Injection

```python
from createagents.infra.config import LoggingConfig, StandardLogger

# Create logger adapter
python_logger = LoggingConfig.get_logger(__name__)
logger_interface = StandardLogger(python_logger)

# Inject into tool
my_tool = MyCustomTool(logger=logger_interface)
```

______________________________________________________________________

## 🔒 Security and Privacy

- **Sanitization**: API keys, passwords, and tokens are automatically masked (e.g. `[API_KEY_REDACTED]`).
- **Filters**: In production, you can configure filters to log errors only.

______________________________________________________________________

## ⚙️ Environment Variables

Configure logging behavior declaratively via environment variables:

| Variable          | Description                                                 | Default        |
| ----------------- | ----------------------------------------------------------- | -------------- |
| `LOG_LEVEL`       | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) | `INFO`         |
| `LOG_TO_FILE`     | Save logs to disk (`true` / `false`)                        | `false`        |
| `LOG_FILE_PATH`   | File path when `LOG_TO_FILE` is active                      | `logs/app.log` |
| `LOG_JSON_FORMAT` | Emit structured JSON logs                                   | `false`        |

______________________________________________________________________

## 📊 Structured JSON Logging (Production)

For production environments with centralized log aggregators (Datadog, CloudWatch, OpenTelemetry, ELK), enable JSON output:

```python
from createagents import LoggingConfig

LoggingConfig.configure(json_format=True)
```

Or via environment variable:

```bash
export LOG_JSON_FORMAT=true
```

Output format example:

```json
{
  "timestamp": "2026-08-25 10:00:00,000",
  "level": "INFO",
  "logger": "createagents.infra.adapters.openai.adapter",
  "message": "Chat request completed successfully",
  "module": "chat_adapter",
  "function": "chat",
  "line": 85
}
```

When an exception is logged with `exc_info=True`, the sanitized `"exception"` traceback string is automatically included in the JSON object.

______________________________________________________________________

## 🔍 Components that Use Logging

### Use Cases

Use cases receive `LoggerInterface` injected by `AgentComposer` and fall back to `NullLogger` when omitted — allowing the application layer to log without importing `infra`:

```python
class ChatWithAgentUseCase:
    def __init__(
        self,
        chat_repository: ChatRepository,
        logger: LoggerInterface | None = None,
    ):
        self._logger = logger or NullLogger()
```

### `ToolExecutor`

`ToolExecutor` in the domain uses `LoggerInterface` to trace tool executions:

```python
class ToolExecutor:
    def __init__(self, tools: list[BaseTool], logger: LoggerInterface) -> None:
        self.__logger = logger

    async def execute_tool(self, tool_name: str, **kwargs):
        self.__logger.info("Attempting to execute tool: '%s'", tool_name)
        # ...
```

### Stream Handlers (OpenAI / Ollama)

Streaming handlers log connection events, chunk statistics, and errors:

```python
class OpenAIStreamHandler:
    def __init__(self, *args, **kwargs):
        self._logger = LoggingConfig.get_logger(__name__)

    async def handle_stream(self, *args, **kwargs):
        self._logger.debug('Starting streaming response')
        # ...
```

______________________________________________________________________

## 💡 Best Practices

1. **Keep Disabled by Default**: Never enable global logging inside library components; let the consumer application configure logging.
2. **Appropriate Log Levels**:
   - `DEBUG`: Detailed execution trace and internal variables
   - `INFO`: Normal operational events (agent initialized, tool executed)
   - `WARNING`: Recoverable anomalies
   - `ERROR`: Operations that failed to complete
   - `CRITICAL`: Severe unrecoverable system failures
3. **Never Log Secrets Explicitly**: Avoid logging passwords or raw tokens.
4. **Lazy String Formatting**: Use `%s` interpolation (`logger.debug('Processing %s items in %sms', len(items), duration_ms)`) instead of eager f-strings to avoid string interpolation overhead when log level is disabled.
5. **Identify Call Sites**: Always instantiate loggers with `LoggingConfig.get_logger(__name__)` to ensure accurate `module`, `function`, and `line` information in structured logs.

______________________________________________________________________

**Version:** 0.3.0 | **Updated:** 2026-08-27
