# CLI Architecture

Technical documentation for the Presentation layer (CLI) of CreateAgents AI.

______________________________________________________________________

## 📐 Overview

The CLI implements the **Command Pattern** to process user input and execute actions cleanly decoupled from the application layer through interfaces.

```
ChatCLIApplication (orchestrator)
    ├── CommandRegistry (handler registry)
    ├── TerminalRenderer (UI / rendering)
    ├── InputReader (input reading)
    └── CommandHandlers (specific processors)
        ├── ChatCommandHandler
        ├── HelpCommandHandler
        ├── MetricsCommandHandler
        ├── ConfigsCommandHandler
        ├── ToolsCommandHandler
        └── ClearCommandHandler
```

______________________________________________________________________

## 🎯 Core Components

### 1. ChatCLIApplication

**Responsibility**: Main CLI lifecycle orchestrator.

**Location**: `src/createagents/presentation/cli/application/chat_cli_app.py`

```python
class ChatCLIApplication:
    """Main CLI application orchestrator.

    Responsibility: Orchestrate the CLI application lifecycle.
    This follows:
    - SRP: Only handles application orchestration
    - DIP: Depends on abstractions (CommandHandler interface)
    - OCP: New commands can be added by registering new handlers
    """

    def __init__(self, agent: 'AgentFacade'):
        self._agent = agent
        self._renderer = TerminalRenderer()
        self._input_reader = InputReader()
        self._registry = CommandRegistry()
        self._setup_commands()

    def run(self) -> None:
        """Start the CLI application main loop."""
        # Main execution loop
```

**Key Methods**:

- `__init__(agent)` - Initializes UI components and command registry
- `_setup_commands()` - Registers command handlers in precedence order
- `run()` - Main interactive loop
- `_is_exit_command(input)` - Identifies termination commands

______________________________________________________________________

### 2. CommandHandler (Interface)

**Responsibility**: Abstract base class for command handlers.

**Location**: `src/createagents/presentation/cli/commands/base_command.py`

```python
class CommandHandler(ABC):
    """Abstract base class for command handlers.

    This implements the Command Pattern, allowing dynamic
    command registration and execution.
    """

    def __init__(self, renderer: TerminalRenderer):
        self._renderer = renderer

    def can_handle(self, user_input: str) -> bool:
        """Check if this handler can process the input (default: alias matching)."""
        return self._normalize_input(user_input) in self.get_aliases()

    @abstractmethod
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the command."""
        pass

    @abstractmethod
    def get_aliases(self) -> list[str]:
        """Get command aliases."""
        pass
```

______________________________________________________________________

### 3. CommandRegistry

**Responsibility**: Registration and resolution of command handlers.

**Location**: `src/createagents/presentation/cli/application/command_registry.py`

```python
class CommandRegistry:
    """Registry for command handlers.

    Responsibility: Maintain and resolve command handlers.
    This follows OCP: new handlers can be added without modification.
    """

    def __init__(self):
        self._handlers: list[CommandHandler] = []

    def register(self, handler: CommandHandler) -> None:
        """Register a command handler."""
        self._handlers.append(handler)

    def find_handler(self, user_input: str) -> CommandHandler | None:
        """Find the first handler that can process the input."""
        for handler in self._handlers:
            if handler.can_handle(user_input):
                return handler
        return None
```

**Registration Order Principle**:
Handlers are registered from most specific to most generic. `ChatCommandHandler` must always be registered last as the fallback handler.

______________________________________________________________________

### 4. Command Handlers

#### ChatCommandHandler

Processes normal chat messages with real-time streaming support.

```python
class ChatCommandHandler(CommandHandler):
    """Handles regular chat messages (default handler)."""

    def can_handle(self, user_input: str) -> bool:
        return bool(user_input.strip())

    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        asyncio.run(self.__run_chat(agent, user_input))

    def get_aliases(self) -> list[str]:
        return []
```

#### HelpCommandHandler

Displays system help and available commands index.

```python
class HelpCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        self._render_markdown(_HELP_TEXT)

    def get_aliases(self) -> list[str]:
        return ['/help', 'help']
```

#### MetricsCommandHandler

Renders latency and token usage metrics.

```python
class MetricsCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        metrics = agent.get_metrics()
        # Formats Markdown table and renders via self._render_markdown(...)
```

______________________________________________________________________

### 5. TerminalRenderer

**Responsibility**: Terminal output formatting, panels, and live streaming.

**Location**: `src/createagents/presentation/cli/ui/terminal_renderer.py`

```python
class TerminalRenderer:
    """Handles terminal rendering with colors, panels and formatting."""

    def __init__(self, show_timestamps: bool = False):
        self._formatter = TerminalFormatter()
        self._console = Console()
        self._show_timestamps = show_timestamps

    def render_welcome_screen(self) -> None: ...
    def render_prompt(self) -> None: ...
    def render_user_message(self, message: str) -> None: ...
    def render_ai_message(self, message: str) -> None: ...
    async def render_ai_message_streaming(
        self, token_generator: AsyncIterator[str]
    ) -> None: ...
    def render_system_message(self, message: str) -> None: ...
    def render_error(self, message: str) -> None: ...
```

______________________________________________________________________

### 6. Formatters

#### TerminalFormatter

Calculates display widths, wraps text, and builds rounded message panels.

**Location**: `src/createagents/presentation/cli/ui/terminal_formatter.py`

> **Note:** The snippet below illustrates the conceptual interface of `TerminalFormatter`. The full repository implementation performs regex ANSI stripping, word wrapping, and Unicode box styling.

#### MarkdownTerminalFormatter

Converts Markdown headers, tables, lists, and emphasis into styled ANSI terminal output (does not perform code syntax highlighting).

**Location**: `src/createagents/presentation/cli/ui/markdown_formatter.py`

______________________________________________________________________

### 7. ColorScheme

Centralizes ANSI color codes across a 256-color palette.

**Location**: `src/createagents/presentation/cli/ui/color_scheme.py`

```python
class ColorScheme:
    """Manages ANSI color codes for terminal output."""

    BLUE: str = '\033[38;5;75m'  # User prompts
    PURPLE: str = '\033[38;5;141m'  # Static AI responses
    GREEN: str = '\033[38;5;84m'  # Success markers
    YELLOW: str = '\033[38;5;221m'  # Warnings / Session interrupts
    RED: str = '\033[38;5;204m'  # Errors
    CYAN: str = '\033[38;5;87m'  # System / Menus
    RESET: str = '\033[0m'
```

______________________________________________________________________

## 🔄 Execution Flow

### 1. Initialization

```
main()
  → ChatCLIApplication(agent)
      → __init__
          → TerminalRenderer()
          → InputReader()
          → CommandRegistry()
          → _setup_commands()
              → registry.register(HelpCommandHandler)
              → registry.register(MetricsCommandHandler)
              → ... (other specific handlers)
              → registry.register(ChatCommandHandler) ← LAST
```

### 2. Main Loop

```
app.run()
  → renderer.render_welcome_screen()
  → while True:
      → renderer.render_prompt()
      → user_input = input_reader.read_user_input()
      → if _is_exit_command(user_input): break
      → handler = registry.find_handler(user_input)
      → handler.execute(agent, user_input)
```

### 3. Command Processing

```
# Example: /metrics
registry.find_handler("/metrics")
  → iterates registered handlers
  → MetricsCommandHandler.can_handle("/metrics") → True
  → returns MetricsCommandHandler

MetricsCommandHandler.execute(agent, "/metrics")
  → metrics = agent.get_metrics()
  → renderer.render_metrics(metrics)
```

### 4. Chat Processing Flow

```
ChatCommandHandler.execute(agent, "Hello")
  → asyncio.run(__run_chat(agent, "Hello"))
      → renderer.render_user_message("Hello")
      → renderer.render_spacer()
      → renderer.render_thinking_indicator()
      → response = await agent.chat("Hello")
      → if isinstance(response, StreamingResponseDTO):
            await renderer.render_ai_message_streaming(response)
        else:
            renderer.clear_thinking_indicator()
            renderer.render_ai_message(MarkdownTerminalFormatter.format(response))
      → renderer.render_spacer()
```

______________________________________________________________________

## 🎨 Architectural Principles

### Single Responsibility (SRP)

Each class owns a single distinct responsibility:

- `ChatCLIApplication`: Lifecycle orchestration
- `CommandRegistry`: Command registration and resolution
- `TerminalRenderer`: UI rendering and formatting
- `CommandHandler`: Specific command execution logic

### Open/Closed (OCP)

Open for extension via new command handlers without modifying existing classes:

```python
class CustomCommandHandler(CommandHandler):
    def can_handle(self, user_input: str) -> bool:
        return user_input.startswith('/custom')

    def execute(self, agent, user_input):
        pass

    def get_aliases(self):
        return ['/custom']


# Registration
registry.register(CustomCommandHandler(renderer))
```

### Dependency Inversion (DIP)

Handlers depend on abstractions (`CommandHandler`), never concrete orchestrator implementations.

### Command Pattern

Each handler encapsulates an action as an object, enabling dynamic dispatch, request queues, and modular extension.

______________________________________________________________________

## 🛠️ Adding New Commands

To extend the CLI with a custom command:

1. **Create the Handler** subclassing `CommandHandler`:

```python
# src/createagents/presentation/cli/commands/my_command.py
from .base_command import CommandHandler


class MyCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        self._renderer.render_system_message('Command executed')

    def get_aliases(self) -> list[str]:
        return ['/mycommand', 'mycommand']
```

2. **Register the Handler** in `ChatCLIApplication._setup_commands`:

```python
# src/createagents/presentation/cli/application/chat_cli_app.py
def _setup_commands(self) -> None:
    self._registry.register(MyCommandHandler(self._renderer))
    # ChatCommandHandler must always be registered last (default fallback)
    self._registry.register(ChatCommandHandler(self._renderer))
```

______________________________________________________________________

## 📊 Testability

```python
from unittest.mock import Mock

from createagents.presentation.cli.commands import HelpCommandHandler


def test_help_command_handler():
    mock_renderer = Mock()
    handler = HelpCommandHandler(mock_renderer)

    assert handler.can_handle('/help') is True
    assert handler.can_handle('other') is False

    handler.execute(Mock(), '/help')
    mock_renderer.render_system_message.assert_called_once()
```

______________________________________________________________________

## 💡 Best Practices

1. **Registration Order**: Specific handlers first, `ChatCommandHandler` last as fallback.
2. **Use Renderer**: Never invoke `print()` directly; route output through `self._renderer`.
3. **Normalize Input**: Always use `self._normalize_input(user_input)` for alias comparisons.
4. **Async Awareness**: Chat is asynchronous; use `asyncio.run()` when entering from sync handler methods.

______________________________________________________________________

## 📚 Next Steps

- [Async Guide](async-guide.md)
- [API Reference - Commands](../reference/commands.md)
- [Contributing Guide](contribute.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-27
