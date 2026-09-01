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
    _GPT5_MODELS_WITHOUT_SAMPLING: ClassVar[tuple[str, ...]] = (
        'gpt-5',
        'gpt-5-mini',
        'gpt-5-nano',
    )
    _GPT5_MODELS_REQUIRING_NONE_FOR_SAMPLING: ClassVar[tuple[str, ...]] = (
        'gpt-5.1',
        'gpt-5.2',
    )

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
            chat_kwargs.update(self.__build_config_kwargs(model, config))

        return await self.__client.responses.create(**chat_kwargs)

    def __build_config_kwargs(
        self, model: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Translate library config names to valid Responses parameters."""
        config_copy = config.copy()
        config_kwargs: dict[str, Any] = {}

        if 'stream' in config_copy:
            config_kwargs['stream'] = config_copy.pop('stream')

        for api_key, config_key in self._PARAM_MAPPING.items():
            if config_key in config_copy:
                config_copy[api_key] = config_copy.pop(config_key)

        for key, config_data in config_copy.items():
            if key == 'top_k':
                continue
            if key in {
                'temperature',
                'top_p',
            } and not self.__supports_sampling(model, config_copy):
                self.__logger.debug(
                    "Ignoring '%s' for OpenAI model '%s'",
                    key,
                    model,
                )
                continue
            if key == 'reasoning':
                config_kwargs['reasoning'] = (
                    config_data.copy()
                    if isinstance(config_data, dict)
                    else {'effort': config_data}
                )
                continue
            if key == 'max_output_tokens' and (
                isinstance(config_data, bool)
                or (isinstance(config_data, int) and config_data <= 0)
            ):
                continue
            config_kwargs[key] = config_data

        return config_kwargs

    @classmethod
    def __supports_sampling(cls, model: str, config: dict[str, Any]) -> bool:
        """Return whether sampling fields are valid for the selected model."""
        normalized_model = model.lower()

        if cls.__matches_model(
            normalized_model, cls._GPT5_MODELS_WITHOUT_SAMPLING
        ):
            return False
        if not cls.__matches_model(
            normalized_model, cls._GPT5_MODELS_REQUIRING_NONE_FOR_SAMPLING
        ):
            return True

        reasoning = config.get('reasoning')
        if reasoning is None:
            return True
        if isinstance(reasoning, dict):
            return reasoning.get('effort') == 'none'
        return isinstance(reasoning, str) and reasoning == 'none'

    @staticmethod
    def __matches_model(model: str, prefixes: tuple[str, ...]) -> bool:
        """Match a model alias and its dated snapshots."""
        return any(
            model == prefix or model.startswith(f'{prefix}-')
            for prefix in prefixes
        )
