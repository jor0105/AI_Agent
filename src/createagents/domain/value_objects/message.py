from dataclasses import dataclass
from enum import StrEnum


class MessageRole(StrEnum):
    """Enum to define possible roles in a message."""

    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    TOOL = 'tool'  # For tool execution results

    def __str__(self) -> str:
        """Return the string value of the role."""
        return self.value


@dataclass(frozen=True)
class Message:
    """Represents a message in the chat as a Value Object.

    It is immutable to ensure data integrity.
    """

    role: MessageRole
    content: str

    def __post_init__(self) -> None:
        """Validates the message data."""
        if not isinstance(self.role, MessageRole):
            # TypeError would be more precise, but `Message` is exported from
            # `createagents.domain` and callers already catch ValueError.
            # Changing it is a breaking change, not a lint fix.
            raise ValueError(  # noqa: TRY004
                "The 'role' must be an instance of MessageRole."
            )

        if not self.content or not self.content.strip():
            raise ValueError('The message content cannot be empty.')

    def to_dict(self) -> dict[str, str]:
        """Converts the message to a dictionary.

        Returns:
            A dictionary with the role and content.
        """
        return {'role': self.role.value, 'content': self.content}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> 'Message':
        """Creates a Message instance from a dictionary.

        Args:
            data: A dictionary containing 'role' and 'content'.

        Returns:
            A new Message instance.

        Raises:
            ValueError: If the dictionary does not contain the required fields.
        """
        if 'role' not in data or 'content' not in data:
            raise ValueError(
                "The dictionary must contain 'role' and 'content'."
            )

        try:
            role = MessageRole(data['role'])
        except ValueError as e:
            raise ValueError(
                f"Invalid role: '{data['role']}'. "
                f'Valid values are: {[r.value for r in MessageRole]}'
            ) from e

        return cls(role=role, content=data['content'])
