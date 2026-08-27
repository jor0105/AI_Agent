from typing import TYPE_CHECKING

from .base_command import CommandHandler

if TYPE_CHECKING:
    from ..protocols import AgentFacade


class ToolsCommandHandler(CommandHandler):
    """Handles the /tools command.

    Responsibility: Display available tools.
    This follows SRP by handling only tools-related functionality.
    """

    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the tools command.

        Args:
            agent: The agent facade.
            user_input: The user's input string.
        """
        tools = agent.get_all_available_tools()
        tools_str = '## Available Tools\n\n'
        if not tools:
            tools_str += '_No tools configured for this agent._'
        else:
            for name, desc in tools.items():
                tools_str += f'**{name}**\n{desc}\n\n'
        self._render_markdown(tools_str)

    def get_aliases(self) -> list[str]:
        """Get tools command aliases."""
        return ['/tools', 'get_tools']
