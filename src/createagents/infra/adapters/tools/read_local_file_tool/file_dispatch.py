from pathlib import Path

from .....domain import FileReadException
from ....config import LoggingConfig
from .constants import (
    DOCUMENT_EXTENSIONS,
    EXCEL_EXTENSIONS,
    TEXT_EXTENSIONS,
    FileType,
)
from .encoding_utils import read_text_file
from .tabular_readers import (
    read_csv_file,
    read_excel_file,
    read_parquet_file,
)
from .unstructured_readers import read_document_file, read_pdf_file

logger = LoggingConfig.get_logger(__name__)


def determine_file_type(extension: str) -> FileType:
    """Determine the file type based on extension.

    Args:
        extension: File extension without the dot (lowercase).

    Returns:
        FileType enum value.
    """
    if extension in TEXT_EXTENSIONS:
        return FileType.TEXT
    if extension == 'csv':
        return FileType.CSV
    if extension in EXCEL_EXTENSIONS:
        return FileType.EXCEL
    if extension == 'pdf':
        return FileType.PDF
    if extension == 'parquet':
        return FileType.PARQUET
    if extension in DOCUMENT_EXTENSIONS:
        return FileType.DOCUMENT
    return FileType.UNKNOWN


def _read_as_text_fallback(file_path: Path) -> str:
    """Read an unknown file type as text, translating decode failures.

    Args:
        file_path: Path to the file.

    Returns:
        File content as string.

    Raises:
        FileReadException: If the file cannot be decoded as text.
    """
    try:
        content = read_text_file(file_path)
        logger.warning(
            'Unknown file type, successfully read as text: %s',
            file_path.suffix,
        )
        return content
    except UnicodeDecodeError as e:
        raise FileReadException(
            str(file_path),
            f'Cannot decode file as text: {e.reason}',
        ) from e


def read_file_by_type(file_path: Path, file_type: FileType) -> str:
    """Read file content based on its type.

    Args:
        file_path: Path to the file.
        file_type: Type of the file.

    Returns:
        File content as string.

    Raises:
        FileReadException: If file reading fails.
    """
    try:
        if file_type == FileType.TEXT:
            return read_text_file(file_path)
        if file_type == FileType.CSV:
            return read_csv_file(file_path)
        if file_type == FileType.EXCEL:
            return read_excel_file(file_path)
        if file_type == FileType.PDF:
            return read_pdf_file(file_path)
        if file_type == FileType.PARQUET:
            return read_parquet_file(file_path)
        if file_type == FileType.DOCUMENT:
            return read_document_file(file_path)
        # Try as text file (fallback for unknown types)
        return _read_as_text_fallback(file_path)
    except FileReadException:
        raise
    except (ValueError, OSError, RuntimeError) as e:
        raise FileReadException(
            str(file_path),
            f'{type(e).__name__}: {e}',
        ) from e
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f'{type(e).__name__}: {e}',
        ) from e
