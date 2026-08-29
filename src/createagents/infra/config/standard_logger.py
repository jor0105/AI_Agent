import logging
from typing import Any, override

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

    @override
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    @override
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    @override
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    @override
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    @override
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)


def create_logger(name: str) -> LoggerInterface:
    """Create a logger instance.

    Args:
        name: The name for the logger (usually __name__).

    Returns:
        A LoggerInterface implementation.

    """
    python_logger = LoggingConfig.get_logger(name)
    return StandardLogger(python_logger)
