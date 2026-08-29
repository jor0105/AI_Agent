from typing import Any, override

from .logger_interface import LoggerInterface


class NullLogger(LoggerInterface):
    """A logger that discards every record.

    Used as the default for application components constructed without an
    explicit logger, so the application layer never has to reach into the
    infrastructure layer just to obtain one. The composition root injects a
    real logger for the production path.
    """

    @override
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard a debug message."""

    @override
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard an info message."""

    @override
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard a warning message."""

    @override
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard an error message."""

    @override
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard a critical message."""

    @override
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Discard an exception message."""
