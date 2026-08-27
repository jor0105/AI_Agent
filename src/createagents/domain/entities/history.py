from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from ..value_objects.message import Message, MessageRole


@dataclass
class History:
    """Manages the chat message history.

    This entity encapsulates the logic for limiting the history size.

    It uses a deque with `maxlen` for optimized performance, automatically
    removing old messages without recreating the data structure.

    Thread-safe: Uses a lock to ensure safe concurrent access to messages.
    """

    max_size: int = 10
    _messages: deque[Message] = field(default_factory=deque)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the history with a deque and a lock.

        Raises:
            ValueError: If max_size is not positive.
        """
        if not isinstance(self.max_size, int) or self.max_size <= 0:
            raise ValueError(
                "The history's max size must be greater than zero."
            )

        messages = list(self._messages) if self._messages else []
        self._messages = deque(messages, maxlen=self.max_size)
        self._lock = Lock()

    def add(self, message: Message) -> None:
        """Adds a message to the history.

        The deque with `maxlen` automatically maintains the size limit.

        Args:
            message: The message to be added.
        """
        if not isinstance(message, Message):
            raise TypeError('Only Message objects can be added.')

        with self._lock:
            self._messages.append(message)

    def add_user_message(self, content: str) -> None:
        """A shortcut to add a user message.

        Args:
            content: The content of the message.
        """
        message = Message(role=MessageRole.USER, content=content)
        self.add(message)

    def add_assistant_message(self, content: str) -> None:
        """A shortcut to add an assistant message.

        Args:
            content: The content of the message.
        """
        message = Message(role=MessageRole.ASSISTANT, content=content)
        self.add(message)

    def add_system_message(self, content: str) -> None:
        """A shortcut to add a system message.

        Args:
            content: The content of the message.
        """
        message = Message(role=MessageRole.SYSTEM, content=content)
        self.add(message)

    def add_tool_message(self, content: str) -> None:
        """A shortcut to add a tool message (tool execution result).

        Args:
            content: The content of the tool result.
        """
        message = Message(role=MessageRole.TOOL, content=content)
        self.add(message)

    def clear(self) -> None:
        """Clears all messages from the history."""
        with self._lock:
            self._messages.clear()

    def get_messages(self) -> list[Message]:
        """Returns a copy of the message list.

        Returns:
            A list of messages.
        """
        with self._lock:
            return list(self._messages)

    def to_dict_list(self) -> list[dict[str, str]]:
        """Converts the history to a list of dictionaries.

        Returns:
            A list of dictionaries, each with a role and content.
        """
        with self._lock:
            return [message.to_dict() for message in self._messages]

    @classmethod
    def from_dict_list(
        cls, data: list[dict[str, str]], max_size: int
    ) -> 'History':
        """Creates a History instance from a list of dictionaries.

        Args:
            data: A list of dictionaries, each with 'role' and 'content'.
            max_size: The maximum size of the history.

        Returns:
            A new History instance.
        """
        history = cls(max_size=max_size)
        for item in data:
            message = Message.from_dict(item)
            history.add(message)
        return history

    def __len__(self) -> int:
        """Return the number of messages in the history."""
        with self._lock:
            return len(self._messages)

    def __bool__(self) -> bool:
        """Return True if the history is not empty."""
        with self._lock:
            return bool(self._messages)
