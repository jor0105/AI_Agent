from importlib import import_module
from typing import Protocol, cast

from ....config import LoggingConfig
from .constants import TIKTOKEN_ENCODING

logger = LoggingConfig.get_logger(__name__)


class _TokenEncoding(Protocol):
    """Subset of a tiktoken encoding required by this module."""

    def encode(self, text: str) -> list[int]:
        """Encode text into token identifiers."""


class _TiktokenModule(Protocol):
    """Subset of the optional tiktoken module used by this module."""

    def get_encoding(self, encoding_name: str) -> _TokenEncoding:
        """Load a named token encoding."""


def initialize_tiktoken() -> _TokenEncoding:
    """Initialize the tiktoken encoder for token counting.

    Returns:
        Initialized tiktoken encoding instance.

    Raises:
        RuntimeError: If tiktoken is not installed or initialization fails.

    """
    try:
        tiktoken = cast(_TiktokenModule, import_module('tiktoken'))
        encoding = tiktoken.get_encoding(TIKTOKEN_ENCODING)
        logger.debug('Initialized tiktoken encoder: %s', TIKTOKEN_ENCODING)
        return encoding
    except ImportError as e:
        raise RuntimeError(
            'tiktoken is required for token counting. '
            'Install with: pip install createagents[file-tools]'
        ) from e
    except (ValueError, TypeError) as e:
        error_msg = f'Failed to initialize tiktoken encoder: {e}'
        logger.exception('Failed to initialize tiktoken encoder')
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f'Unexpected error initializing tiktoken encoder: {e}'
        logger.exception('Unexpected error initializing tiktoken encoder')
        raise RuntimeError(error_msg) from e


def count_tokens(text: str, encoding: _TokenEncoding) -> int:
    """Count the number of tokens in the given text.

    Args:
        text: Text content to count tokens for.
        encoding: Tiktoken encoding instance.

    Returns:
        Number of tokens in the text.

    """
    try:
        return len(encoding.encode(text))
    except (ValueError, TypeError):
        logger.exception('Error counting tokens')
        # Fallback to character-based estimation
        # (rough approximation: ~4 chars per token)
        return len(text) // 4
