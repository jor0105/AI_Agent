from typing import TYPE_CHECKING, Any, override

from .base_command import CommandHandler

if TYPE_CHECKING:
    from ..protocols import AgentFacade

_PREVIEW_MAX_CHARS = 50


class ConfigsCommandHandler(CommandHandler):
    """Handles the /configs command.

    Responsibility: Display agent configurations.
    This follows SRP by handling only config-related functionality.
    """

    @override
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the configs command.

        Args:
            agent: The agent facade.
            user_input: The user's input string.

        """
        config_str = '## Agent Configuration\n\n'
        for key, value in agent.get_configs().items():
            if key == 'history' and isinstance(value, list):
                config_str += self.__format_history(key, value)
            else:
                config_str += f'**{key}:** {value}\n'
        self._render_markdown(config_str)

    @staticmethod
    def __format_history(key: str, history: list[dict[str, Any]]) -> str:
        """Render the history entry as a count plus one preview per message.

        Args:
            key: The configuration key being rendered.
            history: The stored messages, each with a role and content.

        Returns:
            The Markdown block for this entry, ending in a blank line.

        """
        block = f'**{key}:** {len(history)} messages in history\n\n'
        for message in history:
            role = message.get('role', 'unknown')
            content = str(message.get('content', ''))
            preview = (
                f'{content[:_PREVIEW_MAX_CHARS]}...'
                if len(content) > _PREVIEW_MAX_CHARS
                else content
            )
            single_line = preview.replace('\n', ' ')
            # Indented bullets give the messages a visual hierarchy under
            # the entry they belong to.
            block += f'  - **{role}**: {single_line}\n'
        return block + '\n'

    @override
    def get_aliases(self) -> list[str]:
        """Get configs command aliases."""
        return ['/configs', 'get_configs']
