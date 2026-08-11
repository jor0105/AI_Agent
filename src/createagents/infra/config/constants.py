"""Centralized configuration constants for the infrastructure layer."""

from typing import Final

DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_MAX_TOOL_ITERATIONS: Final[int] = 100
DEFAULT_OLLAMA_HOST: Final[str] = 'http://localhost:11434'
