from ..commands import CommandHandler


class CommandRegistry:
    """Registry for command handlers.

    Responsibility: Register and resolve command handlers.
    This follows:
    - SRP: Only handles command registration and lookup
    - OCP: New commands can be added without modifying this class
    """

    def __init__(self) -> None:
        """Initialize the command registry."""
        self._handlers: list[CommandHandler] = []

    def register(self, handler: CommandHandler) -> None:
        """Register a command handler.

        Args:
            handler: The command handler to register.
        """
        self._handlers.append(handler)

    def find_handler(self, user_input: str) -> CommandHandler | None:
        """Find appropriate handler for user input.

        Searches through registered handlers in order and returns the first
        handler that can handle the input.

        Args:
            user_input: The user's input string.

        Returns:
            The first matching CommandHandler, or None if no match found.
        """
        for handler in self._handlers:
            if handler.can_handle(user_input):
                return handler
        return None

    def get_all_handlers(self) -> list[CommandHandler]:
        """Get all registered handlers.

        Returns:
            List of all registered command handlers.
        """
        return self._handlers.copy()

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
