from typing import TYPE_CHECKING, override

from .base_command import CommandHandler

if TYPE_CHECKING:
    from ..protocols import AgentFacade

_HELP_TEXT = """
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Type 'exit' or 'quit' to close the application.
"""


class HelpCommandHandler(CommandHandler):
    """Handles the /help command.

    Responsibility: Display help information to the user.
    This follows SRP by handling only help-related functionality.
    """

    @override
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the help command.

        Args:
            agent: The agent facade (not used for help).
            user_input: The user's input string.

        """
        self._render_markdown(_HELP_TEXT)

    @override
    def get_aliases(self) -> list[str]:
        """Get help command aliases."""
        return ['/help', 'help']
