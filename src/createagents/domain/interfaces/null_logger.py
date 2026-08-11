from typing import Any

from .logger_interface import LoggerInterface


class NullLogger(LoggerInterface):
    """A logger that discards every record.

    Used as the default for application components constructed without an
    explicit logger, so the application layer never has to reach into the
    infrastructure layer just to obtain one. The composition root injects a
    real logger for the production path.
    """

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard a debug message."""

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard an info message."""

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard a warning message."""

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard an error message."""

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard a critical message."""

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard an exception message."""
