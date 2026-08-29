from dataclasses import dataclass, field
from typing import Any

from ..exceptions import (
    InvalidConfigTypeException,
    InvalidProviderException,
    UnsupportedConfigException,
)
from ..value_objects import (
    BaseTool,
    SupportedConfigs,
    SupportedProviders,
)
from .history import History


@dataclass
class Agent:
    """Represents an AI agent in the domain.

    Responsibilities:
    - Maintain the agent's identity and configuration.
    - Manage conversation history via the `History` value object.
    - Ensure the integrity of the agent's data via domain validations.

    Business validations are executed in `__post_init__`.
    History management logic is delegated to the `History` value object.
    """

    provider: str
    model: str
    name: str | None = None
    instructions: str | None = None
    config: dict[str, Any] | None = None
    tools: list[BaseTool] | None = None
    history: History = field(default_factory=History)

    def __post_init__(self) -> None:
        """Initialize history (if needed) and validate agent configuration.

        Raises:
            InvalidProviderException: if the provider is not supported.
            UnsupportedConfigException: if a configuration key is unsupported.
            InvalidConfigTypeException: if a configuration value has an invalid type.

        """
        if not isinstance(self.history, History):
            self.history = History()

        available_providers = SupportedProviders.get_available_providers()
        if self.provider.lower() not in available_providers:
            raise InvalidProviderException(
                self.provider, set(available_providers)
            )

        if self.config:
            for key, value in self.config.items():
                available_configs = SupportedConfigs.get_available_configs()
                if key not in available_configs:
                    raise UnsupportedConfigException(
                        key, set(available_configs)
                    )

                if not isinstance(
                    value, (int, float, str, bool, list, dict, type(None))
                ):
                    raise InvalidConfigTypeException(key, type(value))

                SupportedConfigs.validate_config(key, value)

    def add_user_message(self, content: str) -> None:
        """Add a user message to history."""
        self.history.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to history."""
        self.history.add_assistant_message(content)

    def add_tool_message(self, content: str) -> None:
        """Add a tool message to history."""
        self.history.add_tool_message(content)

    def clear_history(self) -> None:
        """Clear all messages from history."""
        self.history.clear()
