from collections.abc import AsyncGenerator
from typing import Any, override

from ....application.interfaces import ChatRepository
from ....domain import BaseTool, ChatException, ChatMetrics
from ...config import LoggingConfig
from .ollama_client import OllamaClient, OllamaMessage
from .ollama_handler import OllamaHandler
from .ollama_stream_handler import OllamaStreamHandler


class OllamaChatAdapter(ChatRepository):
    """An adapter for communicating with Ollama.

    This adapter supports native tool calling using Ollama's built-in
    function calling capability (similar to OpenAI).

    Tool calling flow:
    1. Send tools schema to Ollama API
    2. Model decides whether to call tools based on the query
    3. If tool calls are detected, execute them
    4. Send tool results back to model
    5. Model generates final response
    """

    def __init__(self) -> None:
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__client = OllamaClient()
        self.__metrics: list[ChatMetrics] = []

        self.__logger.info('Ollama adapter initialized')

    @override
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        """Send a message to Ollama and return the response.

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI settings (supports 'stream': True/False).
            history: The conversation history.
            user_ask: The user's question.
            tools: Optional list of tools (native Ollama API).

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
                'Starting chat with model %s on Ollama.', model
            )

            messages: list[OllamaMessage] = []
            if instructions and instructions.strip():
                messages.append({'role': 'system', 'content': instructions})
            messages.extend(history)
            messages.append({'role': 'user', 'content': user_ask})

            # Check if streaming mode is enabled
            if config and config.get('stream'):
                stream_handler = OllamaStreamHandler(
                    self.__client, self.__metrics
                )
                self.__logger.debug('Streaming mode enabled for Ollama')
                return stream_handler.handle_stream(
                    model, messages, config, tools
                )

            # Non-streaming mode - Tool calling loop
            handler = OllamaHandler(self.__client, self.__metrics)
            result: str = await handler.execute_tool_loop(
                model, messages, config, tools
            )
            return result

        except ChatException:
            raise
        except Exception as e:
            self.__logger.exception(
                'An error occurred while communicating with Ollama'
            )
            raise ChatException(
                f'An error occurred while communicating with Ollama: {e!s}',
                original_error=e,
            ) from e

    @override
    def get_metrics(self) -> list[ChatMetrics]:
        """Return the list of collected metrics.

        Returns:
            List[ChatMetrics]: The list of metrics.

        """
        return self.__metrics.copy()
