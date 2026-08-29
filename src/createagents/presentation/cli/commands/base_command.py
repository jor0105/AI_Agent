from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..ui import MarkdownTerminalFormatter

if TYPE_CHECKING:
    from ..protocols import AgentFacade
    from ..ui import TerminalRenderer


class CommandHandler(ABC):
    """Abstract base class for CLI command handlers.

    This interface follows:
    - ISP: Minimal interface with only necessary methods
    - DIP: High-level modules depend on this abstraction
    - OCP: New commands can be added without modifying existing code

    A subclass declares its aliases and its behaviour; matching the input
    against those aliases is handled here, so a command that is selected by
    alias -- which is every command except the default chat handler -- has
    nothing to implement beyond `execute` and `get_aliases`.
    """

    def __init__(self, renderer: 'TerminalRenderer') -> None:
        """Initialize the command handler.

        Args:
            renderer: The terminal renderer for output.

        """
        self._renderer = renderer

    def can_handle(self, user_input: str) -> bool:
        """Check if this handler can process the given input.

        Matches the normalized input against `get_aliases`. Override only for
        a handler selected by something other than an exact alias.

        Args:
            user_input: The user's input string.

        Returns:
            True if this handler can process the input, False otherwise.

        """
        return self._normalize_input(user_input) in self.get_aliases()

    @abstractmethod
    def execute(self, agent: 'AgentFacade', user_input: str) -> Any:
        """Execute the command.

        Args:
            agent: The agent facade.
            user_input: The user's input string.

        Returns:
            Command execution result (can vary by command).

        """

    @abstractmethod
    def get_aliases(self) -> list[str]:
        """Get the list of command aliases.

        Returns:
            List of command aliases (e.g., ['/help', 'help']).

        """

    def _normalize_input(self, user_input: str) -> str:
        """Normalize user input for comparison.

        Args:
            user_input: The raw user input.

        Returns:
            Normalized input (stripped and lowercased).

        """
        return user_input.strip().lower()

    def _render_markdown(self, markdown: str) -> None:
        """Render Markdown as a system message in the terminal.

        Args:
            markdown: The Markdown source to format and display.

        """
        self._renderer.render_system_message(
            MarkdownTerminalFormatter.format(markdown)
        )
