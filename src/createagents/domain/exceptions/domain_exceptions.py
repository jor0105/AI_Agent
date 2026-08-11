from typing import Any


class AgentException(Exception):
    """Base exception for agent-related errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InvalidAgentConfigException(AgentException):
    """Exception raised when the agent configuration is invalid."""

    def __init__(self, field: str, reason: str) -> None:
        message = f"Invalid configuration in field '{field}': {reason}"
        super().__init__(message)


class InvalidModelException(AgentException):
    """Exception raised when the specified AI model is not supported."""

    def __init__(self, model: str) -> None:
        message = f"Unsupported AI model: '{model}'"
        super().__init__(message)


class ChatException(Exception):
    """Base exception for errors during communication with AI."""

    def __init__(
        self, message: str, original_error: Exception | None = None
    ) -> None:
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class AdapterNotFoundException(ChatException):
    """Exception raised when the chat adapter is not found."""

    def __init__(self, adapter_name: str) -> None:
        message = f"Adapter not found: '{adapter_name}'"
        super().__init__(message)


class InvalidProviderException(AgentException):
    """Exception raised when the provider is not supported."""

    def __init__(self, provider: str, available_providers: set[str]) -> None:
        providers = ', '.join(sorted(available_providers))
        message = f"Provider '{provider}' is not available. Available providers: {providers}"
        super().__init__(message)


class UnsupportedConfigException(AgentException):
    """Exception raised when a configuration is not supported."""

    def __init__(self, config_key: str, available_configs: set[str]) -> None:
        configs = ', '.join(sorted(available_configs))
        message = f"Configuration '{config_key}' is not supported. Valid options: {configs}"
        super().__init__(message)


class InvalidConfigTypeException(AgentException):
    """Exception raised when the configuration type is invalid."""

    def __init__(self, config_key: str, value_type: type) -> None:
        message = f"Configuration '{config_key}' has invalid type: {value_type.__name__}"
        super().__init__(message)


class InvalidBaseToolException(AgentException):
    """Exception raised when a provided tool does not match the BaseTool interface."""

    def __init__(self, tool: Any) -> None:
        message = (
            f"Tool '{tool}' is invalid. It must inherit from BaseTool and "
            "implement the attributes 'name' (string type), 'description' "
            "(string type), and the 'execute' method."
        )
        super().__init__(message)


class FileReadException(AgentException):
    """Exception raised when file reading operation fails."""

    def __init__(self, file_path: str, reason: str) -> None:
        message = f"Failed to read file '{file_path}': {reason}"
        super().__init__(message)
