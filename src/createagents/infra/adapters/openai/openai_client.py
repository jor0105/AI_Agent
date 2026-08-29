from typing import Any, ClassVar

from ....domain import ChatException
from ...config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    EnvironmentConfig,
    LoggingConfig,
)
from .client_openai import ClientOpenAI


class OpenAIClient:
    """Handles direct communication with the OpenAI API."""

    _PARAM_MAPPING: ClassVar[dict[str, str]] = {
        'reasoning': 'think',
        'max_output_tokens': 'max_tokens',
    }

    def __init__(self) -> None:
        """Initialize the OpenAI client.

        Raises:
            ChatException: If the API key is missing or invalid.

        """
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__timeout = EnvironmentConfig.get_int_env(
            'OPENAI_TIMEOUT', DEFAULT_TIMEOUT
        )
        self.__max_retries = EnvironmentConfig.get_int_env(
            'OPENAI_MAX_RETRIES', DEFAULT_MAX_RETRIES
        )

        try:
            api_key = EnvironmentConfig.get_api_key(
                ClientOpenAI.API_OPENAI_NAME
            )
            self.__client = ClientOpenAI.get_client(
                api_key,
                timeout=self.__timeout,
                max_retries=self.__max_retries,
            )
            self.__logger.info(
                'OpenAI client initialized (timeout: %ss, max_retries: %s)',
                self.__timeout,
                self.__max_retries,
            )
        except OSError as e:
            self.__logger.exception('Error configuring OpenAI')
            raise ChatException(f'Error configuring OpenAI: {e!s}', e) from e

    async def call_api(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Call the OpenAI Responses API.

        Transport retries are owned by the SDK client, configured from
        `OPENAI_TIMEOUT` and `OPENAI_MAX_RETRIES`.

        Args:
            model: The name of the model.
            instructions: System instructions or prompt.
            messages: A list of messages.
            config: Internal AI configuration.
            tools: Optional list of tool schemas for function calling.

        Returns:
            The API response object.

        """
        chat_kwargs: dict[str, Any] = {
            'model': model,
            'instructions': instructions,
            'input': messages,
        }

        if tools:
            chat_kwargs['tools'] = tools
        if config:
            config_copy = config.copy()

            if 'stream' in config_copy:
                chat_kwargs['stream'] = config_copy.pop('stream')

            for api_key, config_key in self._PARAM_MAPPING.items():
                if config_key in config_copy:
                    config_copy[api_key] = config_copy.pop(config_key)
            for key, config_data in config_copy.items():
                if key == 'reasoning':
                    chat_kwargs['reasoning'] = {'effort': config_data}
                else:
                    chat_kwargs[key] = config_data

        return await self.__client.responses.create(**chat_kwargs)
