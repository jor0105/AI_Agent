"""Centralized logging configuration for the application.

This module provides a configurable logger that can be used
throughout the application for tracking and debugging.

Features:
- Automatic sensitive data filtering
- Log file rotation
- Configuration via environment variables
- Optional structured (JSON) logs
- Different handlers for console and file
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import ClassVar

from .sensitive_data_filter import SensitiveDataFilter

#: Root logger of the distributed package. Derived from `__name__` so a
#: package rename cannot silently detach the null handler installed below.
PACKAGE_LOGGER_NAME: str = __name__.split('.')[0]


class ErrorOnlyFilter(logging.Filter):
    """A filter that only allows ERROR and CRITICAL messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Only allow ERROR and CRITICAL level messages."""
        return record.levelno >= logging.ERROR


class SensitiveDataFormatter(logging.Formatter):
    """A formatter that applies sensitive data filtering.

    This ensures that no sensitive data is logged.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record while filtering for sensitive data."""
        original = super().format(record)
        result: str = SensitiveDataFilter.filter(original)
        return result


class JSONFormatter(logging.Formatter):
    """A formatter for structured JSON logs.

    This is useful for integration with log analysis tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a structured JSON object."""
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        json_str = json.dumps(log_data, ensure_ascii=False)
        result: str = SensitiveDataFilter.filter(json_str)
        return result


class LoggingConfig:
    """A centralized configuration for logging.

    This class provides configured loggers for different modules, featuring:
    - Sensitive data filtering
    - Log file rotation
    - Configuration via environment variables
    """

    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_LOG_PATH = 'logs/app.log'

    _configured: bool = False
    _log_level: int = DEFAULT_LOG_LEVEL
    _handlers: ClassVar[list[logging.Handler]] = []

    @classmethod
    def configure(
        cls,
        level: int | None = None,
        format_string: str | None = None,
        include_timestamp: bool = True,
        log_to_file: bool = False,
        log_file_path: str | None = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        json_format: bool = False,
    ) -> None:
        """Configure the application's logging.

        Args:
            level: The logging level (e.g., DEBUG, INFO).
            format_string: A custom format string (optional).
            include_timestamp: Whether to include a timestamp in the logs.
            log_to_file: Whether to log to a file in addition to the console.
            log_file_path: The path to the log file.
            max_bytes: The maximum file size before rotation (default: 10MB).
            backup_count: The number of backup files to keep (default: 5).
            json_format: Whether to use a structured JSON format.

        """
        # Always reconfigure when called; there is no early return on
        # `cls._configured` by design.
        level = level or cls._get_log_level_from_env()
        log_to_file = (
            log_to_file or os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
        )
        log_file_path = cls._resolve_log_file_path(log_file_path)
        json_format = (
            json_format
            or os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
        )

        cls._log_level = level
        format_string = cls._resolve_format_string(
            format_string, include_timestamp
        )
        root_logger = cls._reset_loggers(level)

        if json_format:
            formatter: logging.Formatter = JSONFormatter()
        else:
            formatter = SensitiveDataFormatter(format_string)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        # At ERROR or CRITICAL, filter out the INFO/WARNING records that the
        # handler level alone would still let through from child loggers.
        if level >= logging.ERROR:
            console_handler.addFilter(ErrorOnlyFilter())

        root_logger.addHandler(console_handler)
        cls._handlers.append(console_handler)

        if log_to_file:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                str(log_file_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8',
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)

            if level >= logging.ERROR:
                file_handler.addFilter(ErrorOnlyFilter())

            root_logger.addHandler(file_handler)
            cls._handlers.append(file_handler)

        cls._configured = True

    @classmethod
    def configure_for_development(cls, level: int = logging.INFO) -> None:
        """Configure logging for development and testing environments.

        This is useful for seeing logs during development, tests, or examples.
        It enables console logging with sensible defaults.
        """
        cls.configure(level=level)

    @staticmethod
    def _resolve_format_string(
        format_string: str | None, include_timestamp: bool
    ) -> str:
        """Resolve log message format pattern."""
        if format_string is not None:
            return format_string
        if include_timestamp:
            return '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        return '%(name)s - %(levelname)s - %(message)s'

    @classmethod
    def _reset_loggers(cls, level: int) -> logging.Logger:
        """Reset root and existing child loggers to the target level."""
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        cls._handlers.clear()

        for logger_name in list(logging.Logger.manager.loggerDict):
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            if level >= logging.ERROR:
                logger.addFilter(ErrorOnlyFilter())

        return root_logger

    @classmethod
    def _resolve_log_file_path(cls, log_file_path: str | None) -> str:
        """Resolve and validate the log file path.

        This method centralizes the logic for path validation to improve readability.

        Args:
            log_file_path: The provided path, or None.

        Returns:
            A valid path as a string.

        """
        default_path = os.getenv('LOG_FILE_PATH', cls.DEFAULT_LOG_PATH)

        if log_file_path is None or isinstance(log_file_path, bool):
            return default_path

        try:
            return str(log_file_path)
        except (ValueError, TypeError):
            return default_path

    @classmethod
    def _get_log_level_from_env(cls) -> int:
        """Retrieve the log level from the LOG_LEVEL environment variable.

        Returns:
            The logging level (default: INFO).

        """
        level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        return level_map.get(level_name, logging.INFO)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Retrieve a logger for the specified module.

        Note: This no longer configures logging automatically.
        The application using the library is responsible for configuring logging.

        Args:
            name: The name of the module (usually `__name__`).

        Returns:
            A standard python logger.

        """
        # Simply return the logger. Configuration is up to the app.
        return logging.getLogger(name)

    @classmethod
    def set_level(cls, level: int) -> None:
        """Adjust the logging level at runtime.

        Args:
            level: The new logging level.

        """
        cls._log_level = level
        logging.getLogger().setLevel(level)

    @classmethod
    def reset(cls) -> None:
        """Reset the logging configuration, which is useful for tests.

        This method removes all handlers and marks the configuration as not set.
        """
        cls._configured = False
        root_logger = logging.getLogger()

        for handler in cls._handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        cls._handlers.clear()
        SensitiveDataFilter.clear_cache()

    @classmethod
    def get_handlers(cls) -> list[logging.Handler]:
        """Return a list of the configured handlers.

        Returns:
            A list of active handlers.

        """
        return cls._handlers.copy()

    @classmethod
    def silence_package_logger(cls) -> None:
        """Keep the library quiet until the host application opts in.

        Without a handler, Python's `lastResort` handler writes WARNING and
        above straight to stderr, so a library that never calls `configure`
        would still print. A `NullHandler` on the package root suppresses
        that without capturing anything, which is the standard practice for
        libraries. Idempotent: repeated calls add no further handlers.
        """
        package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        already_silenced = any(
            isinstance(handler, logging.NullHandler)
            for handler in package_logger.handlers
        )
        if not already_silenced:
            package_logger.addHandler(logging.NullHandler())


# Applied at import time: the package must be silent by default, before any
# consumer code has a chance to emit its first record.
LoggingConfig.silence_package_logger()
