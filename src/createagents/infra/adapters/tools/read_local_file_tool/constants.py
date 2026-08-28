from enum import Enum
from typing import Final


class FileType(Enum):
    """Supported file types for reading."""

    TEXT = 'text'
    CSV = 'csv'
    EXCEL = 'excel'
    PDF = 'pdf'
    PARQUET = 'parquet'
    DOCUMENT = 'document'  # Word, PowerPoint, etc. handled by unstructured
    UNKNOWN = 'unknown'


# Supported file extensions for text-based reading
TEXT_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        'txt',
        'log',
        'md',
        'py',
        'js',
        'html',
        'css',
        'json',
        'xml',
        'yaml',
        'yml',
        'rst',
        'ini',
        'cfg',
        'conf',
        'sh',
        'bash',
        'zsh',
    }
)

EXCEL_EXTENSIONS: Final[frozenset[str]] = frozenset({'xls', 'xlsx', 'xlsm'})

# Document types that unstructured can handle
DOCUMENT_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        'doc',
        'docx',
        'ppt',
        'pptx',
        'odt',
        'epub',
        'msg',
        'rtf',
    }
)

# Maximum file size in bytes (100 MB) as an additional safety check
MAX_FILE_SIZE_BYTES: Final[int] = 100 * 1024 * 1024

# Default encoding for tiktoken
TIKTOKEN_ENCODING: Final[str] = 'cl100k_base'

# Common encodings to try when reading text files
COMMON_ENCODINGS: Final[list[str]] = [
    'utf-8',
    'latin-1',
    'iso-8859-1',
    'cp1252',
    'windows-1252',
]
