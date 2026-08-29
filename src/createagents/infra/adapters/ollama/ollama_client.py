from collections.abc import AsyncIterator
from typing import Any, cast

from ollama import AsyncClient, ChatResponse, Message

from ...config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_OLLAMA_HOST,
    EnvironmentConfig,
    LoggingConfig,
    retry_with_backoff,
)

#: A turn sent to Ollama. Plain dicts cover user/system/tool messages, while
#: assistant turns carrying tool calls must be echoed back as the SDK's own
#: `Message` object for the model to see its previous calls.
#: Declared as an explicit alias so it stays a type even where the `ollama`
#: stubs are unavailable and `Message` degrades to `Any`.
type OllamaMessage = dict[str, Any] | Message


class OllamaClient:
    """Handles direct communication with the Ollama API.

    Streaming and non-streaming calls are separate methods so each caller
    gets a single concrete return type instead of a union it has to narrow
    by inspecting the config.
    """

    def __init__(self) -> None:
        """Configure the client from the environment.

        `OLLAMA_HOST` selects the server and `OLLAMA_MAX_RETRIES` sets how
        many attempts a call gets before the error propagates.
        """
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__host = (
            EnvironmentConfig.get_env('OLLAMA_HOST', DEFAULT_OLLAMA_HOST)
            or DEFAULT_OLLAMA_HOST
        )
        self.__max_retries = EnvironmentConfig.get_int_env(
            'OLLAMA_MAX_RETRIES', DEFAULT_MAX_RETRIES
        )

        # Built once per client so the configured attempt count is honoured;
        # a decorator on the method would freeze it at import time.
        self.__call_with_retry = retry_with_backoff(
            max_attempts=self.__max_retries,
            initial_delay=1.0,
            exceptions=(TimeoutError, ConnectionError, OSError),
        )(self.__request)

    async def call_api(
        self,
        model: str,
        messages: list[OllamaMessage],
        config: dict[str, Any] | None,
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResponse:
        """Request a complete (non-streamed) chat response.

        Args:
            model: The name of the model.
            messages: The conversation to send.
            config: Internal AI configuration.
            tools: Optional tool schemas for function calling.

        Returns:
            The complete chat response.

        """
        result = await self.__call_with_retry(
            model, messages, config, tools, False
        )
        return cast('ChatResponse', result)

    async def stream_api(
        self,
        model: str,
        messages: list[OllamaMessage],
        config: dict[str, Any] | None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[ChatResponse]:
        """Request a streamed chat response.

        Args:
            model: The name of the model.
            messages: The conversation to send.
            config: Internal AI configuration.
            tools: Optional tool schemas for function calling.

        Returns:
            An async iterator over the response chunks.

        """
        result = await self.__call_with_retry(
            model, messages, config, tools, True
        )
        return cast('AsyncIterator[ChatResponse]', result)

    async def __request(
        self,
        model: str,
        messages: list[OllamaMessage],
        config: dict[str, Any] | None,
        tools: list[dict[str, Any]] | None,
        stream: bool,
    ) -> ChatResponse | AsyncIterator[ChatResponse]:
        """Perform a single Ollama chat call without retrying."""
        try:
            chat_kwargs: dict[str, Any] = {
                'model': model,
                'messages': messages,
                'stream': stream,
            }

            if tools:
                chat_kwargs['tools'] = tools
            if config:
                options = config.copy()
                options.pop('stream', None)
                if 'think' in options:
                    chat_kwargs['think'] = options.pop('think')
                if 'max_tokens' in options:
                    options['num_predict'] = options.pop('max_tokens')
                chat_kwargs['options'] = options

            client = AsyncClient(host=self.__host)
            result: (
                ChatResponse | AsyncIterator[ChatResponse]
            ) = await client.chat(**chat_kwargs)
            return result
        except Exception:
            self.__logger.exception(
                "Error calling Ollama API for model '%s'", model
            )
            raise
