"""The agent contract the CLI depends on.

Declared here, next to its only consumer, rather than imported from
`main.facade`. The CLI is driven by the facade, and the facade's `start_cli`
launches the CLI; importing the concrete `CreateAgent` for a type annotation
closed that loop into an import cycle.

`AgentFacade` is a structural Protocol, so `CreateAgent` satisfies it without
knowing it exists and without any import in either direction. It lists only
the five members the CLI actually calls -- the facade's remaining public
methods are deliberately out of scope (ISP).
"""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ...application.dtos import StreamingResponseDTO
    from ...domain import ChatMetrics


class AgentFacade(Protocol):
    """The subset of the agent facade that the terminal CLI drives."""

    async def chat(self, message: str) -> 'str | StreamingResponseDTO':
        """Send a message to the agent and return its response.

        Args:
            message: The user's message.

        Returns:
            The response text, or a `StreamingResponseDTO` when the agent is
            configured for streaming.

        """
        ...

    def get_configs(self) -> dict[str, Any]:
        """Return the agent's configuration.

        Returns:
            The agent's configuration values, keyed by name.

        """
        ...

    def get_all_available_tools(self) -> dict[str, str]:
        """Return every tool the agent can call.

        Returns:
            Tool names mapped to their descriptions.

        """
        ...

    def clear_history(self) -> None:
        """Discard the conversation history."""
        ...

    def get_metrics(self) -> list['ChatMetrics']:
        """Return the metrics collected for this session.

        Returns:
            One `ChatMetrics` entry per recorded chat operation.

        """
        ...
