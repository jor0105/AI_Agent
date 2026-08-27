import logging
from typing import Any

from ...domain.interfaces import LoggerInterface
from .logging_config import LoggingConfig


class StandardLogger(LoggerInterface):
    """Standard logger implementation using Python's logging module.

    This adapter wraps Python's standard logging.Logger to implement
    the domain's LoggerInterface, following the Adapter pattern.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize with a Python logger instance.

        Args:
            logger: The underlying Python logger to use.
        """
        self._logger = logger

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message with the active exception traceback."""
        # This adapter intentionally delegates; the exception handler lives
        # at the call site, not here.
        self._logger.error(message, *args, exc_info=True, **kwargs)


def create_logger(name: str) -> LoggerInterface:
    """Factory function to create a logger instance.

    Args:
        name: The name for the logger (usually __name__).

    Returns:
        A LoggerInterface implementation.
    """
    python_logger = LoggingConfig.get_logger(name)
    return StandardLogger(python_logger)
