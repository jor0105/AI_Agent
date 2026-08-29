from pathlib import Path
from typing import Any, ClassVar, override

from .....domain import BaseTool, FileReadException
from ....config import EnvironmentConfig, LoggingConfig
from .constants import MAX_FILE_SIZE_BYTES

IMPORT_ERROR = None

try:
    from .file_dispatch import determine_file_type, read_file_by_type
    from .token_utils import count_tokens, initialize_tiktoken

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = e


class ReadLocalFileTool(BaseTool):
    """Secure local file reader with token validation.

    Reads files with multiple validation layers:
    - Token limit enforcement
    - File type validation
    - Comprehensive error handling

    Supports formats: txt, csv, excel (xls/xlsx/xlsm), pdf, parquet,
    and common text files.
    """

    name = 'readlocalfile'
    description = (
        'Use this tool to read local files from the system. '
        'Supports text files (txt, md, py, etc.), CSV, Excel, PDF and '
        'Parquet formats. The tool validates file size in tokens to prevent '
        'overload. Input must include the absolute or relative file path and '
        'optionally the maximum number of tokens allowed (default: 30000).'
    )
    parameters: ClassVar[dict[str, Any]] = {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'Absolute or relative path to the file to read.',
            },
            'max_tokens': {
                'type': 'integer',
                'description': (
                    'Maximum number of tokens allowed in the file content. '
                    'Files exceeding this limit will be rejected.'
                ),
                'default': 30000,
            },
        },
        'required': ['path'],
    }

    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_BYTES

    @classmethod
    def _get_allowed_base_dir(cls) -> Path:
        """Return the resolved sandbox directory for file reading."""
        base = EnvironmentConfig.get_env('FILE_TOOL_BASE_DIR') or '.'
        return Path(base).resolve()

    def __init__(self) -> None:
        """Initialize the ReadLocalFileTool.

        Raises:
            RuntimeError: If tiktoken encoder initialization fails or
                          dependencies are missing.

        """
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError(
                'ReadLocalFileTool requires optional dependencies. '
                'Optional dependencies for ReadLocalFileTool are not installed.\n'
                'Install them using: uv sync --locked --extra file-tools or pip install "createagents[file-tools]"\n'
                f'Missing dependencies error: {IMPORT_ERROR}'
            )

        self.__logger = LoggingConfig.get_logger(__name__)
        self.__encoding = initialize_tiktoken()

    @override
    def execute(
        self,
        path: str,
        max_tokens: int = 30000,
    ) -> str:
        """Execute the file reading operation with validation.

        Args:
            path: Absolute or relative path to the file.
            max_tokens: Maximum tokens allowed (default: 30000).

        Returns:
            File content as string, or error message if operation fails.

        Error Messages:
            - File not found: File doesn't exist
            - Path is a directory: Path points to a directory
            - File too large: File exceeds size limit
            - Content exceeds token limit: Content has too many tokens
            - Various file-specific errors

        """
        self.__logger.info(
            "Executing file read: path='%s', max_tokens=%s",
            path,
            max_tokens,
        )

        try:
            file_path = Path(path).resolve()
            validation_error = self.__validate_file_path(file_path, path)
            if validation_error is not None:
                return validation_error

            # Determine file type and read content
            extension = file_path.suffix.lstrip('.').lower() or 'txt'
            self.__logger.debug('Processing file as type: %s', extension)

            file_type = determine_file_type(extension)
            content = read_file_by_type(file_path, file_type)

            token_count = count_tokens(content, self.__encoding)
            self.__logger.debug('File content has %s tokens', token_count)

            if token_count > max_tokens:
                return self.__format_error(
                    'Content exceeds token limit',
                    f'{path} has {token_count} tokens (max: {max_tokens}). '
                    f'Consider increasing max_tokens or processing in chunks',
                )

            self.__logger.info(
                "Successfully read file '%s': %s characters, %s tokens",
                path,
                len(content),
                token_count,
            )
            return content

        except FileNotFoundError:
            return self.__format_error('File not found', path)

        except FileReadException as e:
            return self.__format_error('File read error', e.message)

        except PermissionError:
            return self.__format_error('Permission denied', path)

        except (OSError, RuntimeError, ValueError) as e:
            return self.__format_error('File processing error', str(e))

        except Exception as e:
            error_msg = (
                f'[ReadLocalFileTool Error] Unexpected error: '
                f'{type(e).__name__}: {e}'
            )
            self.__logger.exception(error_msg)
            return error_msg

    def __validate_file_path(
        self, file_path: Path, raw_path: str
    ) -> str | None:
        """Validate accessibility, existence, and size for a target file.

        Args:
            file_path: Resolved target path.
            raw_path: Original path argument for error formatting.

        Returns:
            An error message string if invalid, or None if valid.

        """
        allowed_dir = self._get_allowed_base_dir()
        if not file_path.is_relative_to(allowed_dir):
            return self.__format_error(
                'Access denied',
                f"Path '{raw_path}' is outside the allowed directory '{allowed_dir}'",
            )

        if not file_path.exists():
            return self.__format_error('File not found', raw_path)

        if not file_path.is_file():
            return self.__format_error('Path is a directory', raw_path)

        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            return self.__format_error(
                'File too large',
                f'{raw_path} is {size_mb:.2f} MB (max: {max_mb:.2f} MB)',
            )

        return None

    def __format_error(self, error_type: str, details: str) -> str:
        """Format a consistent error message.

        Args:
            error_type: Type of error that occurred.
            details: Detailed information about the error.

        Returns:
            Formatted error message string.

        """
        error_msg = f'[ReadLocalFileTool Error] {error_type}: {details}'
        self.__logger.error(error_msg)
        return error_msg
