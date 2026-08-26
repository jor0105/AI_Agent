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

    def __init__(self, agent: 'CreateAgent'):
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

#### MarkdownTerminalFormatter

Converts Markdown headers, tables, code blocks, and emphasis into styled ANSI terminal output.

**Location**: `src/createagents/presentation/cli/ui/markdown_formatter.py`

______________________________________________________________________

### 7. ColorScheme

Centralizes ANSI color codes across a 256-color palette.

**Location**: `src/createagents/presentation/cli/ui/color_scheme.py`

```python
class ColorScheme:
    """Manages ANSI color codes for terminal output."""

    BLUE: str = '\033[38;5;75m'  # User prompts
    PURPLE: str = '\033[38;5;141m'  # AI messages
    GREEN: str = '\033[38;5;84m'  # Success
    YELLOW: str = '\033[38;5;221m'  # Warnings / System
    RED: str = '\033[38;5;204m'  # Errors
    CYAN: str = '\033[38;5;87m'  # System
    RESET: str = '\033[0m'
```

______________________________________________________________________

## 🔄 Execution Flow

```
main()
  → ChatCLIApplication(agent)
      → TerminalRenderer()
      → CommandRegistry()
      → _setup_commands()
          → Register specific handlers (/help, /metrics, etc.)
          → Register ChatCommandHandler (LAST)
  → app.run()
      → Main loop reading input
      → Registry resolves handler
      → Handler executes action
```

______________________________________________________________________

## 🛠️ Adding New Commands

### Step 1: Create Handler

```python
# src/createagents/presentation/cli/commands/my_command.py
from .base_command import CommandHandler


class MyCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        result = self._my_logic(agent)
        self._renderer.render_system_message(result)

    def get_aliases(self) -> list[str]:
        return ['/mycommand', 'mycommand']

    def _my_logic(self, agent):
        return 'Command executed'
```

### Step 2: Register in `_setup_commands`

```python
# src/createagents/presentation/cli/application/chat_cli_app.py
def _setup_commands(self) -> None:
    self._registry.register(MyCommandHandler(self._renderer))
    # ChatCommandHandler remains last
    self._registry.register(ChatCommandHandler(self._renderer))
```

______________________________________________________________________

## 💡 Best Practices

1. **Registration Order**: Specific handlers first, `ChatCommandHandler` last.
2. **Use Renderer**: Never invoke `print()` directly in presentation code; route output through `self._renderer`.
3. **Normalize Input**: Always use `self._normalize_input(user_input)` for alias comparisons.
4. **Async Awareness**: Wrap coroutines with `asyncio.run()` when invoked from synchronous handler entrypoints.

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
