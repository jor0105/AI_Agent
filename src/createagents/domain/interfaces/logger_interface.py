from abc import ABC, abstractmethod
from typing import Any


class LoggerInterface(ABC):
    """Abstract interface for logging functionality.

    This interface defines the contract that any logging implementation
    must follow. It allows the domain layer to use logging without
    depending on specific infrastructure implementations.
    """

    @abstractmethod
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: The message to log.
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra).
        """

    @abstractmethod
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: The message to log.
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra).
        """

    @abstractmethod
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: The message to log.
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra).
        """

    @abstractmethod
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: The message to log.
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra).
        """

    @abstractmethod
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message.

        Args:
            message: The message to log.
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra).
        """

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message with the active exception traceback.

        Must only be called from inside an exception handler. The default
        implementation delegates to `error` with `exc_info` enabled, so
        existing implementations remain valid without overriding it.

        Args:
            message: The message to log.
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., extra).
        """
        kwargs.setdefault('exc_info', True)
        self.error(message, *args, **kwargs)
