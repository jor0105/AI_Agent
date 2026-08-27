from typing import TYPE_CHECKING

from ....infra.config import create_logger
from ..commands import (
    ChatCommandHandler,
    ClearCommandHandler,
    ConfigsCommandHandler,
    HelpCommandHandler,
    MetricsCommandHandler,
    ToolsCommandHandler,
)
from ..io import InputReader
from ..ui import TerminalRenderer
from .command_registry import CommandRegistry

if TYPE_CHECKING:
    from ..protocols import AgentFacade


class ChatCLIApplication:
    """Main CLI application orchestrator.

    Responsibility: Orchestrate the CLI application lifecycle.
    This follows:
    - SRP: Only handles application orchestration
    - DIP: Depends on abstractions (CommandHandler interface)
    - OCP: New commands can be added by registering new handlers
    """

    def __init__(self, agent: 'AgentFacade') -> None:
        """Initialize the CLI application.

        Args:
            agent: The agent facade to interact with.
        """
        self._agent = agent
        self._renderer = TerminalRenderer()
        self._input_reader = InputReader()
        self._registry = CommandRegistry()
        self._logger = create_logger(__name__)
        self._setup_commands()

    def _setup_commands(self) -> None:
        """Register all command handlers.

        This method follows OCP: to add new commands, just register them here.
        The order matters - more specific commands should be registered first,
        and ChatCommandHandler (default) should be last.
        """
        # System commands
        self._registry.register(HelpCommandHandler(self._renderer))
        self._registry.register(MetricsCommandHandler(self._renderer))
        self._registry.register(ConfigsCommandHandler(self._renderer))
        self._registry.register(ToolsCommandHandler(self._renderer))
        self._registry.register(ClearCommandHandler(self._renderer))
        # Default handler (must be last)
        self._registry.register(ChatCommandHandler(self._renderer))

    def run(self) -> None:
        """Start the CLI application main loop.

        This is the main entry point for the CLI application.
        """
        self._renderer.render_welcome_screen()
        while True:
            try:
                # Display prompt
                self._renderer.render_prompt()
                self._renderer.render_input_indicator()
                # Read user input
                user_input = self._input_reader.read_user_input('')
                # Clear input lines for cleaner UI
                self._renderer.clear_input_lines(2)
                # Skip empty input
                if not user_input.strip():
                    continue
                # Check for exit command
                if self._is_exit_command(user_input):
                    self._renderer.render_goodbye()
                    break
                # Find and execute appropriate handler
                handler = self._registry.find_handler(user_input)
                if handler:
                    handler.execute(self._agent, user_input)
                else:
                    # This should never happen if ChatCommandHandler is registered
                    self._renderer.render_error(
                        'No handler found for this command.'
                    )
            except KeyboardInterrupt:
                self._renderer.render_interrupt()
                break
            except Exception as e:
                self._logger.exception('Unhandled error in CLI command loop')
                self._renderer.render_error(str(e))

    def _is_exit_command(self, user_input: str) -> bool:
        """Check if input is an exit command.

        Args:
            user_input: The user's input string.

        Returns:
            True if input is an exit command, False otherwise.
        """
        normalized = user_input.strip().lower()
        return normalized in ('exit', 'quit')
