# Arquitetura da CLI

Documentação técnica da camada Presentation (CLI) do CreateAgents AI.

______________________________________________________________________

## 📐 Visão Geral

A CLI segue o **Command Pattern** para processar entrada do usuário e executar ações. É totalmente desacoplada da camada de aplicação através de interfaces.

```
ChatCLIApplication (orquestrador)
    ├── CommandRegistry (registro de comandos)
    ├── TerminalRenderer (UI/renderização)
    ├── InputReader (leitura de entrada)
    └── CommandHandlers (processadores específicos)
        ├── ChatCommandHandler
        ├── HelpCommandHandler
        ├── MetricsCommandHandler
        ├── ConfigsCommandHandler
        ├── ToolsCommandHandler
        └── ClearCommandHandler
```

______________________________________________________________________

## 🎯 Componentes Principais

### 1. ChatCLIApplication

**Responsabilidade**: Orquestrador principal do ciclo de vida da CLI.

**Localização**: `src/createagents/presentation/cli/application/chat_cli_app.py`

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
        # Loop principal
```

**Métodos**:

- `__init__(agent)` - Inicializa componentes
- `_setup_commands()` - Registra handlers de comandos
- `run()` - Loop principal da aplicação
- `_is_exit_command(input)` - Verifica comandos de saída

______________________________________________________________________

### 2. CommandHandler (Interface)

**Responsabilidade**: Interface abstrata para handlers de comandos.

**Localização**: `src/createagents/presentation/cli/commands/base_command.py`

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

**Responsabilidade**: Registro e resolução de comandos.

**Localização**: `src/createagents/presentation/cli/application/command_registry.py`

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

**Padrão de Registro**:
Os handlers são registrados em ordem, do mais específico ao mais genérico. O `ChatCommandHandler` deve ser sempre o último (handler padrão de fallback).

______________________________________________________________________

### 4. Command Handlers

#### ChatCommandHandler

**Responsabilidade**: Processar mensagens de chat (handler padrão).

```python
class ChatCommandHandler(CommandHandler):
    """Handles regular chat messages (default handler)."""

    def can_handle(self, user_input: str) -> bool:
        # Aceita qualquer entrada não-vazia (fallback)
        return bool(user_input.strip())

    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        # Processa chat e streaming
        asyncio.run(self.__run_chat(agent, user_input))

    def get_aliases(self) -> list[str]:
        return []
```

#### HelpCommandHandler

**Responsabilidade**: Exibir ajuda e lista de comandos.

```python
class HelpCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        self._render_markdown(_HELP_TEXT)

    def get_aliases(self) -> list[str]:
        return ['/help', 'help']
```

#### MetricsCommandHandler

**Responsabilidade**: Exibir métricas de performance.

```python
class MetricsCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        metrics = agent.get_metrics()
        # Constrói tabela Markdown e exibe via self._render_markdown(...)
```

_(Outros handlers como ConfigsCommandHandler, ToolsCommandHandler e ClearCommandHandler seguem estrutura similar)_

______________________________________________________________________

### 5. TerminalRenderer

**Responsabilidade**: Renderização de UI no terminal.

**Localização**: `src/createagents/presentation/cli/ui/terminal_renderer.py`

```python
class TerminalRenderer:
    """Handles terminal rendering with colors, panels and formatting.

    Responsibility: Encapsulate all terminal output logic.
    This follows SRP by handling only rendering concerns.
    """

    def __init__(self, show_timestamps: bool = False):
        self._formatter = TerminalFormatter()
        self._console = Console()
        self._show_timestamps = show_timestamps

    def render_welcome_screen(self) -> None:
        """Display welcome message."""

    def render_prompt(self) -> None:
        """Display user input prompt."""

    def render_user_message(self, message: str) -> None:
        """Render a user message in a right-aligned rounded box."""

    def render_ai_message(self, message: str) -> None:
        """Render a static AI message in a left-aligned rounded box."""

    async def render_ai_message_streaming(
        self, token_generator: AsyncIterator[str]
    ) -> None:
        """Render AI tokens in real time inside a Rich live panel."""

    def render_system_message(self, message: str) -> None:
        """Render a system message."""

    def render_error(self, message: str) -> None:
        """Render an error message."""
```

**Métodos de Renderização**:

- `render_welcome_screen()` - Tela de boas-vindas com banner ASCII
- `render_prompt()` - Prompt de entrada
- `render_input_indicator()` - Indicador de entrada `▶`
- `render_user_message(msg)` - Balão azul alinhado à direita
- `render_ai_message(msg)` - Balão roxo alinhado à esquerda
- `render_ai_message_streaming(gen)` - Painel Rich Live com streaming token a token
- `render_thinking_indicator()` - Indicador "AI is thinking..."
- `clear_thinking_indicator()` - Limpa a linha de pensamento
- `render_system_message(msg)` - Balão ciano do sistema
- `render_success_message(msg)` - Balão verde de sucesso
- `render_error(msg)` - Mensagem de erro formatada
- `render_goodbye()` - Mensagem de despedida
- `render_interrupt()` - Mensagem de encerramento via Ctrl+C

______________________________________________________________________

### 6. Formatters

#### TerminalFormatter

**Responsabilidade**: Formatação de balões arredondados e cálculo de largura.

**Localização**: `src/createagents/presentation/cli/ui/terminal_formatter.py`

```python
class TerminalFormatter:
    """Handles terminal text formatting and display width calculations."""

    @staticmethod
    def get_display_width(text: str) -> int:
        """Calcula largura visual considerando caracteres largos e ignorando ANSI."""

    @staticmethod
    def wrap_text(text: str, max_width: int, subsequent_indent: str = '') -> list[str]:
        """Quebra linhas preservando indentação e largura do terminal."""

    @staticmethod
    def format_rounded_box(text: str, color: str, align: str = 'left', ...) -> str:
        """Envolve o texto em uma caixa arredondada com timestamp e ícone."""
```

#### MarkdownTerminalFormatter

**Responsabilidade**: Formatação de Markdown para saída ANSI colorida no terminal.

**Localização**: `src/createagents/presentation/cli/ui/markdown_formatter.py`

```python
class MarkdownTerminalFormatter:
    """Renders Markdown as ANSI-styled text for the interactive CLI."""

    @staticmethod
    def format(text: str) -> str:
        """Converte headers, listas, tabelas e ênfases em estilos ANSI."""
```

______________________________________________________________________

### 7. ColorScheme

**Responsabilidade**: Centraliza códigos de cores ANSI (paleta 256 cores) e métodos semânticos.

**Localização**: `src/createagents/presentation/cli/ui/color_scheme.py`

```python
class ColorScheme:
    """Manages ANSI color codes for terminal output."""

    BLUE: str = '\033[38;5;75m'  # Mensagens do usuário
    PURPLE: str = '\033[38;5;141m'  # Mensagens da IA
    GREEN: str = '\033[38;5;84m'  # Sucesso
    YELLOW: str = '\033[38;5;221m'  # Avisos
    RED: str = '\033[38;5;204m'  # Erros
    CYAN: str = '\033[38;5;87m'  # Sistema
    GRAY: str = '\033[38;5;245m'  # Texto sutil
    DARK_GRAY: str = '\033[38;5;240m'  # Metadados
    RESET: str = '\033[0m'

    # Métodos semânticos
    # get_user_color(), get_ai_color(), get_system_color(),
    # get_success_color(), get_error_color(), get_timestamp_color()
```

______________________________________________________________________

## 🔄 Fluxo de Execução

### 1. Inicialização

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
              → ... (outros comandos)
              → registry.register(ChatCommandHandler) ← ÚLTIMO
```

### 2. Loop Principal

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

### 3. Processamento de Comando

```
# Exemplo: /metrics
registry.find_handler("/metrics")
  → itera handlers registrados
  → MetricsCommandHandler.can_handle("/metrics") → True
  → retorna MetricsCommandHandler

MetricsCommandHandler.execute(agent, "/metrics")
  → metrics = agent.get_metrics()
  → renderer.render_metrics(metrics)
```

### 4. Processamento de Chat (Streaming)

```
ChatCommandHandler.execute(agent, "Olá")
  → asyncio.run(_async_execute(agent, "Olá"))
      → renderer.render_thinking_indicator()
      → response = await agent.chat("Olá")
      → async for token in response:
          → renderer.render_assistant_token(token)
      → renderer.clear_thinking_indicator()
```

______________________________________________________________________

## 🎨 Princípios Arquiteturais

### Single Responsibility (SRP)

Cada classe tem uma responsabilidade única:

- `ChatCLIApplication`: Orquestração
- `CommandRegistry`: Registro e resolução
- `TerminalRenderer`: Renderização
- `CommandHandler`: Processamento de comando específico

### Open/Closed (OCP)

Aberto para extensão via novos handlers:

```python
# Adicionar novo comando sem modificar código existente
class CustomCommandHandler(CommandHandler):
    def can_handle(self, user_input: str) -> bool:
        return user_input.startswith('/custom')

    def execute(self, agent, user_input):
        # Implementação customizada
        pass

    def get_aliases(self):
        return ['/custom']


# Registrar
registry.register(CustomCommandHandler(renderer))
```

### Dependency Inversion (DIP)

Handlers dependem de abstrações (`CommandHandler`), não implementações concretas.

### Command Pattern

Cada handler encapsula uma ação como objeto, permitindo:

- Parametrização de clientes com diferentes solicitações
- Enfileiramento de solicitações
- Suporte a operações reversíveis

______________________________________________________________________

## 🛠️ Adicionando Novos Comandos

### Passo 1: Criar Handler

```python
# src/createagents/presentation/cli/commands/my_command.py
from .base_command import CommandHandler


class MyCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        # Sua lógica aqui
        result = self._my_logic(agent)
        self._renderer.render_system_message(result)

    def get_aliases(self) -> list[str]:
        return ['/mycommand', 'mycommand']

    def _my_logic(self, agent):
        # Implementação
        return 'Resultado do comando'
```

### Passo 2: Registrar Handler

```python
# src/createagents/presentation/cli/application/chat_cli_app.py
def _setup_commands(self) -> None:
    # ...outros comandos...
    self._registry.register(MyCommandHandler(self._renderer))
    # ChatCommandHandler deve ser sempre último
    self._registry.register(ChatCommandHandler(self._renderer))
```

### Passo 3: Exportar (Opcional)

```python
# src/createagents/presentation/cli/commands/__init__.py
from .my_command import MyCommandHandler

__all__ = [
    # ...outros...
    'MyCommandHandler',
]
```

______________________________________________________________________

## 📊 Testabilidade

A arquitetura permite fácil testabilidade:

```python
import pytest
from unittest.mock import Mock


def test_help_command_handler():
    # Mock renderer
    mock_renderer = Mock()
    handler = HelpCommandHandler(mock_renderer)

    # Mock agent
    mock_agent = Mock()

    # Test can_handle
    assert handler.can_handle('/help') == True
    assert handler.can_handle('other') == False

    # Test execute
    handler.execute(mock_agent, '/help')
    mock_renderer.render_system_message.assert_called_once()
```

______________________________________________________________________

## 💡 Best Practices

1. **Handler Registration Order**: Específico → Genérico
2. **ChatCommandHandler Last**: Sempre registre como último (fallback)
3. **Use Renderer**: Nunca faça `print()` diretamente, use `self._renderer`
4. **Normalize Input**: Use `_normalize_input()` para comparações
5. **Async Awareness**: Chat é assíncrono, use `asyncio.run()` se necessário

______________________________________________________________________

## 📚 Próximos Passos

- [Guia Async](async-guide.md)
- [API Reference - Commands](../reference/commands.md)
- [Contribuindo](contribute.md)

______________________________________________________________________

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
