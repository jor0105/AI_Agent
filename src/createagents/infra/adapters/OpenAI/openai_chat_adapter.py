from collections.abc import AsyncGenerator
from typing import Any

from ....application.interfaces import ChatRepository
from ....domain import BaseTool, ChatException, ChatMetrics
from ...config import LoggingConfig
from .openai_client import OpenAIClient
from .openai_handler import OpenAIHandler
from .openai_stream_handler import OpenAIStreamHandler


class OpenAIChatAdapter(ChatRepository):
    """Initialize the OpenAI adapter."""

    def __init__(self) -> None:
        """Initialize the OpenAI adapter.

        Raises:
            ChatException: If the API key is missing or invalid.
        """
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: list[ChatMetrics] = []

        self.__client = OpenAIClient()

    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        """Sends a message to OpenAI and returns the response.

        Implements tool calling loop:
        1. Send message to LLM
        2. If LLM requests tool calls, execute them
        3. Send tool results back to LLM
        4. Repeat until LLM provides final response

        Streaming mode (config={'stream': True}):
        - Returns a Generator that yields tokens as they arrive

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI configuration (supports 'stream': True/False).
            history: The conversation history.
            user_ask: The user's question.
            tools: Optional list of tools available to the agent.

        Returns:
            Union[str, AsyncGenerator[str, None]]:
                - str: Complete response (if stream=False or not specified)
                - AsyncGenerator[str, None]: Token stream (if stream=True)

        Raises:
            ChatException: If a communication error occurs or if streaming
                is used with tool calling.
        """
        try:
            self.__logger.debug(
                'Starting chat with model %s on OpenAI.', model
            )

            messages = history.copy()
            messages.append({'role': 'user', 'content': user_ask})

            # Check if streaming mode is enabled
            if config and config.get('stream'):
                stream_handler = OpenAIStreamHandler(
                    self.__client, self.__metrics
                )
                return stream_handler.handle_stream(
                    model, instructions, messages, config, tools
                )

            handler = OpenAIHandler(self.__client, self.__metrics)
            return await handler.execute_tool_loop(
                model, instructions, messages, config, tools
            )

        except ChatException:
            raise
        except Exception as e:
            self.__logger.exception(
                'An error occurred while communicating with OpenAI'
            )
            raise ChatException(
                f'An error occurred while communicating with OpenAI: {e!s}',
                original_error=e,
            ) from e

    def get_metrics(self) -> list[ChatMetrics]:
        """Return the list of collected metrics.

        Returns:
            List[ChatMetrics]: The list of metrics.
        """
        return self.__metrics.copy()
