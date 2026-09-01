from collections.abc import Callable
from typing import Any, ClassVar

from ..exceptions import InvalidAgentConfigException


class SupportedConfigs:
    """Manages and validates supported configurations for AI agents.

    Responsibilities:
    - Define the supported configurations.
    - Validate the values of specific configurations.
    - Provide an interface for automatic validation.
    """

    __AVAILABLE_CONFIGS: ClassVar[set[str]] = {
        'temperature',
        'max_tokens',
        'top_p',
        'think',
        'top_k',
        'stream',
    }

    @classmethod
    def get_available_configs(cls) -> set[str]:
        """Return the set of supported configurations.

        Returns:
            A set containing the names of available configurations.

        """
        return cls.__AVAILABLE_CONFIGS.copy()

    @staticmethod
    def validate_temperature(value: float | None) -> None:
        """Validate the 'temperature' parameter.

        Args:
            value: The temperature value, which must be between 0.0 and 2.0.

        Raises:
            InvalidAgentConfigException: If the value is outside the allowed
                range or of the wrong type.

        """
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not (0.0 <= float(value) <= 2.0)
        ):
            raise InvalidAgentConfigException(
                'temperature', 'must be a float between 0.0 and 2.0'
            )

    @staticmethod
    def validate_max_tokens(value: int | None) -> None:
        """Validate the 'max_tokens' parameter.

        Args:
            value: The max_tokens value, which must be an integer greater than zero.

        Raises:
            InvalidAgentConfigException: If the value is invalid.

        """
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
        ):
            raise InvalidAgentConfigException(
                'max_tokens', 'must be an integer greater than zero'
            )

    @staticmethod
    def validate_top_p(value: float | None) -> None:
        """Validate the 'top_p' parameter.

        Args:
            value: The top_p value, which must be between 0.0 and 1.0.

        Raises:
            InvalidAgentConfigException: If the value is outside the allowed
                range or of the wrong type.

        """
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not (0.0 <= float(value) <= 1.0)
        ):
            raise InvalidAgentConfigException(
                'top_p', 'must be a float between 0.0 and 1.0'
            )

    @staticmethod
    def validate_think(value: bool | str | None) -> None:
        """Validate the 'think' parameter.

        The `think` option accepts:
        - Ollama provider: a boolean (True/False) or string ("high", "low", "medium")
        - OpenAI provider: a string ("high", "low", "medium")

        Args:
            value: The think value to validate (or None).

        Raises:
            InvalidAgentConfigException: If the value does not match the allowed shapes.

        """
        if value is None:
            return

        # Booleans are accepted by the Ollama provider.
        if isinstance(value, bool):
            return

        # string is allowed for both Ollama and OpenAI (must be "high", "low", or "medium")
        if isinstance(value, str):
            if value.lower() not in {'high', 'low', 'medium'}:
                raise InvalidAgentConfigException(
                    'think',
                    'must be a boolean (for Ollama) or string "high"/"low"/"medium" '
                    '(for both Ollama and OpenAI Providers)',
                )
            return

        raise InvalidAgentConfigException(
            'think',
            'must be a boolean (for Ollama) or string "high"/"low"/"medium" '
            '(for both Ollama and OpenAI Providers)',
        )

    @staticmethod
    def validate_top_k(value: int | None) -> None:
        """Validate the 'top_k' parameter.

        Args:
            value: The top_k value, which must be an integer greater than zero.

        Raises:
            InvalidAgentConfigException: If the value is invalid.

        """
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
        ):
            raise InvalidAgentConfigException(
                'top_k', 'must be an integer greater than zero'
            )

    @staticmethod
    def validate_stream(value: bool | None) -> None:
        """Validate the 'stream' parameter.

        Args:
            value: The stream value, which must be a boolean.

        Raises:
            InvalidAgentConfigException: If the value is not a boolean.

        """
        if value is not None and not isinstance(value, bool):
            raise InvalidAgentConfigException('stream', 'must be a boolean')

    @classmethod
    def validate_config(cls, key: str, value: Any) -> None:
        """Validate a specific configuration based on its key.

        Args:
            key: The name of the configuration.
            value: The value of the configuration.

        Raises:
            InvalidAgentConfigException: If the validation fails.

        """
        validators: dict[str, Callable[[Any], None]] = {
            'think': cls.validate_think,
            'temperature': cls.validate_temperature,
            'max_tokens': cls.validate_max_tokens,
            'top_p': cls.validate_top_p,
            'top_k': cls.validate_top_k,
            'stream': cls.validate_stream,
        }
        validator = validators.get(key)
        if validator:
            validator(value)
