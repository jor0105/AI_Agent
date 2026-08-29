import asyncio
from typing import TYPE_CHECKING, override

from ....application import StreamingResponseDTO
from ....infra.config import create_logger
from ..ui import MarkdownTerminalFormatter
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ..protocols import AgentFacade

_logger = create_logger(__name__)


class ChatCommandHandler(CommandHandler):
    """Handles regular chat messages (default handler).

    Responsibility: Process regular chat messages.
    This follows SRP by handling only chat-related functionality.
    """

    @override
    def can_handle(self, user_input: str) -> bool:
        """Accept every non-empty input.

        This is the fallback handler rather than an alias-matched command, so
        it replaces the base class's alias check. It must be registered last.
        """
        return bool(user_input.strip())

    @override
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the chat command.

        Args:
            agent: The agent facade.
            user_input: The user's input string.

        """
        asyncio.run(self.__run_chat(agent, user_input))

    async def __run_chat(self, agent: 'AgentFacade', user_input: str) -> None:
        """Send one turn to the agent and render the reply.

        Args:
            agent: The agent facade.
            user_input: The user's input string.

        """
        self._renderer.render_user_message(user_input)
        self._renderer.render_spacer()
        self._renderer.render_thinking_indicator()

        try:
            response = await agent.chat(user_input)

            if isinstance(response, StreamingResponseDTO):
                # The renderer clears the thinking indicator itself once the
                # first token arrives, so the wait stays visible until then.
                await self._renderer.render_ai_message_streaming(response)
            else:
                self._renderer.clear_thinking_indicator()
                self._renderer.render_ai_message(
                    MarkdownTerminalFormatter.format(response)
                )

        except Exception as e:
            _logger.exception('Chat turn failed')
            self._renderer.clear_thinking_indicator()
            self._renderer.render_ai_message(f'Error: {e!s}')

        self._renderer.render_spacer()

    @override
    def get_aliases(self) -> list[str]:
        """Get chat command aliases.

        Returns empty list as this is the default handler.
        """
        return []
