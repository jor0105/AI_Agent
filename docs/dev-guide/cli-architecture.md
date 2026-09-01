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

    def __init__(self, agent: 'AgentFacade'):
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
    def render_thinking_indicator(self) -> None: ...
    def clear_thinking_indicator(self) -> None: ...
    def render_system_message(self, message: str) -> None: ...
    def render_success_message(self, message: str) -> None: ...
    def render_error(self, message: str) -> None: ...
```

______________________________________________________________________

### 6. Formatters

#### TerminalFormatter

**Responsabilidade**: Formatação de balões arredondados e cálculo de largura.

**Localização**: `src/createagents/presentation/cli/ui/terminal_formatter.py`

> **Nota:** As assinaturas abaixo ilustram a interface conceitual do `TerminalFormatter`. A implementação completa no repositório realiza a remoção de sequências ANSI via regex, quebra de linha inteligente e molduras Unicode.

```python
class TerminalFormatter:
    """Handles terminal text formatting and display width calculations."""

    @staticmethod
    def get_display_width(text: str) -> int:
        """Calcula largura visual considerando caracteres largos e ignorando ANSI."""
        return len(text)

    @staticmethod
    def wrap_text(
        text: str, max_width: int, subsequent_indent: str = ''
    ) -> list[str]:
        """Quebra linhas preservando indentação e largura do terminal."""
        return [text]

    @staticmethod
    def format_rounded_box(
        text: str,
        color: str,
        align: str = 'left',
        icon: str = '',
        timestamp: str = '',
    ) -> str:
        """Envolve o texto em uma caixa arredondada com timestamp e ícone."""
        return text
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
        return text
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

#### Encerramento de sessão

Além dos comandos `exit` e `quit`, `Ctrl+D` gera `EOFError` e encerra a
sessão de forma controlada: a CLI renderiza a despedida e sai do loop sem
registrar o evento como um erro genérico. `Ctrl+C` continua renderizando a
mensagem de interrupção antes de encerrar.

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

### 4. Processamento de Chat

```
ChatCommandHandler.execute(agent, "Olá")
  → asyncio.run(__run_chat(agent, "Olá"))
      → renderer.render_user_message("Olá")
      → renderer.render_spacer()
      → renderer.render_thinking_indicator()
      → response = await agent.chat("Olá")
      → if isinstance(response, StreamingResponseDTO):
            await renderer.render_ai_message_streaming(response)
        else:
            renderer.clear_thinking_indicator()
            renderer.render_ai_message(MarkdownTerminalFormatter.format(response))
      → renderer.render_spacer()
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

Para estender a CLI com um novo comando:

1. **Crie o Handler** herdando de `CommandHandler`:

```python
# src/createagents/presentation/cli/commands/my_command.py
from .base_command import CommandHandler


class MyCommandHandler(CommandHandler):
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        self._renderer.render_system_message('Resultado do comando')

    def get_aliases(self) -> list[str]:
        return ['/mycommand', 'mycommand']
```

2. **Registre o Handler** em `ChatCLIApplication._setup_commands`:

```python
# src/createagents/presentation/cli/application/chat_cli_app.py
def _setup_commands(self) -> None:
    self._registry.register(MyCommandHandler(self._renderer))
    # ChatCommandHandler é sempre registrado por último (fallback padrão)
    self._registry.register(ChatCommandHandler(self._renderer))
```

______________________________________________________________________

## 📊 Testabilidade

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

**Versão:** 0.2.0 | **Atualização:** 2026-08-31
