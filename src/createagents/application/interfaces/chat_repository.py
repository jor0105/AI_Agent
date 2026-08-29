from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from ...domain import BaseTool, ChatMetrics


class ChatRepository(ABC):
    """Interface for chat repositories."""

    @abstractmethod
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        """Send a message to the chat model and get a response.

        Args:
            model: The name of the model to use.
            instructions: System instructions for the agent.
            config: Configuration parameters for the model.
            tools: List of tools available to the agent.
            history: Chat history.
            user_ask: The user's message.

        Returns:
            Union[str, AsyncGenerator[str, None]]: The model's response.
                - str: Complete response (if stream=False)
                - AsyncGenerator: Token stream (if stream=True)

        """

    @abstractmethod
    def get_metrics(self) -> list[ChatMetrics]:
        """Return the collected metrics for this repository.

        Returns:
            List of ChatMetrics collected during interactions.

        """
