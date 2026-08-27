from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ...domain import BaseTool, InvalidBaseToolException


def _validate_tool_reference(tool: str | BaseTool) -> None:
    """Check that a tool reference is usable, without resolving it.

    A reference is either the registered name of a system tool or a ready
    `BaseTool` instance. Turning a name into an instance needs the tool
    catalog, which lives in the infrastructure layer, so it is done by
    `CreateAgentUseCase` through the `ToolRegistry` port instead.

    Args:
        tool: The tool name or instance supplied by the caller.

    Raises:
        InvalidBaseToolException: If the reference is neither a non-empty
            string nor a well-formed `BaseTool`.
    """
    if isinstance(tool, str):
        if not tool.strip():
            raise InvalidBaseToolException(tool)
        return

    if not isinstance(tool, BaseTool):
        raise InvalidBaseToolException(tool)

    if not callable(getattr(tool, 'execute', None)):
        raise InvalidBaseToolException(tool)

    if not isinstance(tool.name, str) or not tool.name.strip():
        raise InvalidBaseToolException(tool)

    if not isinstance(tool.description, str) or not tool.description.strip():
        raise InvalidBaseToolException(tool)


@dataclass
class CreateAgentInputDTO:
    """DTO for creating a new agent."""

    provider: str
    model: str
    name: str | None = None
    instructions: str | None = None
    config: dict[str, Any] | None = None
    tools: Sequence[str | BaseTool] | None = None
    history_max_size: int = 10

    def validate(self) -> None:
        """Validate the DTO data.

        Tool references are checked for shape only; `CreateAgentUseCase`
        resolves names into instances afterwards.

        Raises:
            ValueError: If any field validation fails.
            InvalidBaseToolException: If a tool reference is malformed.
        """
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError(
                "The 'provider' field is required, must be a string, and cannot be empty."
            )

        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError(
                "The 'model' field is required, must be a string, and cannot be empty."
            )

        if self.name is not None and (
            not isinstance(self.name, str) or not self.name.strip()
        ):
            raise ValueError(
                "The 'name' field must be a valid string and cannot be empty."
            )

        if self.instructions is not None and (
            not isinstance(self.instructions, str)
            or not self.instructions.strip()
        ):
            raise ValueError(
                "The 'instructions' field must be a valid string and cannot be empty."
            )

        if self.config is not None and not isinstance(self.config, dict):
            raise ValueError("The 'config' field must be a dictionary (dict).")

        for tool in self.tools or ():
            _validate_tool_reference(tool)

        if (
            not isinstance(self.history_max_size, int)
            or self.history_max_size <= 0
        ):
            raise ValueError(
                "The 'history_max_size' field must be a positive integer."
            )


@dataclass
class AgentConfigOutputDTO:
    """DTO for returning agent configurations."""

    provider: str
    model: str
    name: str | None
    instructions: str | None
    config: dict[str, Any] | None
    tools: list[BaseTool] | None
    history: list[dict[str, str]]
    history_max_size: int = 10

    def to_dict(self) -> dict[str, Any]:
        """Convert the DTO to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the DTO.
        """
        tool_names = None
        if self.tools:
            tool_names = [tool.name for tool in self.tools]

        return {
            'provider': self.provider,
            'model': self.model,
            'name': self.name,
            'instructions': self.instructions,
            'config': self.config,
            'tools': tool_names,
            'history': self.history,
            'history_max_size': self.history_max_size,
        }


@dataclass
class ChatInputDTO:
    """DTO for chat message input."""

    message: str

    def validate(self) -> None:
        """Validate the DTO data.

        Raises:
            ValueError: If the message is invalid.
        """
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(
                "The 'message' field is required, must be a string, and cannot be empty."
            )


@dataclass
class ChatOutputDTO:
    """DTO for chat response."""

    response: str

    def to_dict(self) -> dict:
        """Convert the DTO to a dictionary.

        Returns:
            Dict: The dictionary representation of the DTO.
        """
        return {
            'response': self.response,
        }
