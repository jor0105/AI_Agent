from typing import TYPE_CHECKING, override

from .base_command import CommandHandler

if TYPE_CHECKING:
    from ..protocols import AgentFacade


class ClearCommandHandler(CommandHandler):
    """Handles the /clear command.

    Responsibility: Clear chat history.
    This follows SRP by handling only clear-related functionality.
    """

    @override
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the clear command.

        Args:
            agent: The agent facade.
            user_input: The user's input string.

        """
        agent.clear_history()
        self._renderer.render_success_message(
            'Chat history cleared successfully!'
        )

    @override
    def get_aliases(self) -> list[str]:
        """Get clear command aliases."""
        return ['/clear', 'clear_history']
