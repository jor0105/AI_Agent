from pathlib import Path
from typing import Any

from .....domain import FileReadException
from ....config import LoggingConfig
from .encoding_utils import candidate_encodings

logger = LoggingConfig.get_logger(__name__)

# Common CSV delimiters to try
CSV_DELIMITERS = [',', ';', '\t', '|']


def _require_pandas(purpose: str) -> Any:
    """Import pandas or fail with the install hint for the file-tools extra."""
    try:
        import pandas as pd
    except ImportError as e:
        raise RuntimeError(
            f'pandas is required for {purpose}. '
            'Install with: pip install createagents[file-tools]'
        ) from e
    return pd


def read_csv_file(file_path: Path) -> str:
    """Read a CSV file with automatic encoding detection and error handling.

    Args:
        file_path: Path to the CSV file.

    Returns:
        CSV content as formatted string.

    Raises:
        FileReadException: If CSV parsing fails with all strategies.
        RuntimeError: If pandas is not installed.
    """
    pd = _require_pandas('CSV reading')

    last_error: Exception | None = None

    # Try different encoding and delimiter combinations
    for encoding in candidate_encodings(file_path):
        for delimiter in CSV_DELIMITERS:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=delimiter,
                    on_bad_lines='skip',  # Skip malformed lines
                    engine='python',  # More flexible parser
                )

                if not df.empty:
                    logger.debug(
                        "Read CSV file with encoding %s, delimiter '%s', shape: %s",
                        encoding,
                        delimiter,
                        df.shape,
                    )
                    result: str = df.to_string(index=False)
                    return result
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                logger.debug(
                    "Failed to read CSV with %s, delimiter '%s': %s",
                    encoding,
                    delimiter,
                    e,
                )
                continue
            except (ValueError, OSError) as e:
                last_error = e
                continue

    # Last resort: try with maximum error tolerance
    try:
        df = pd.read_csv(
            file_path,
            encoding='utf-8',
            encoding_errors='replace',
            on_bad_lines='skip',
            engine='python',
        )
        logger.warning(
            'All encodings/delimiters failed for CSV, '
            'using UTF-8 with character replacement and skipping bad lines'
        )
        fallback_result: str = df.to_string(index=False)
        return fallback_result
    except (ValueError, OSError):
        raise FileReadException(
            str(file_path),
            f'Failed to read CSV with any strategy. Last error: {last_error}',
        ) from last_error


def read_excel_file(file_path: Path) -> str:
    """Read an Excel file with automatic engine detection and error handling.

    Tries multiple engines (openpyxl for .xlsx, xlrd for .xls) and reads
    the first available sheet.

    Args:
        file_path: Path to the Excel file.

    Returns:
        Excel content as formatted string.

    Raises:
        FileReadException: If Excel reading fails with all strategies.
        RuntimeError: If pandas is not installed.
    """
    pd = _require_pandas('Excel reading')

    # Determine which engine to try based on file extension
    extension = file_path.suffix.lower()
    engines_to_try = []

    if extension in ['.xlsx', '.xlsm']:
        engines_to_try = ['openpyxl', 'xlrd']
    elif extension == '.xls':
        engines_to_try = ['xlrd', 'openpyxl']
    else:
        engines_to_try = ['openpyxl', 'xlrd']

    last_error: Exception | None = None

    for engine in engines_to_try:
        try:
            df = pd.read_excel(file_path, sheet_name=0, engine=engine)
            logger.debug(
                'Read Excel file with engine %s, shape: %s', engine, df.shape
            )
            result: str = df.to_string(index=False)
            return result
        except (ValueError, OSError, ImportError) as e:
            last_error = e
            logger.debug('Failed to read Excel with engine %s: %s', engine, e)
            continue

    raise FileReadException(
        str(file_path),
        f'Failed to read Excel file with any engine. Last error: {last_error}',
    ) from last_error


def read_parquet_file(file_path: Path) -> str:
    """Read a Parquet file with automatic engine detection and error handling.

    Tries multiple engines (pyarrow, fastparquet) and handles various
    parquet format variations.

    Args:
        file_path: Path to the Parquet file.

    Returns:
        Parquet content as formatted string.

    Raises:
        FileReadException: If Parquet reading fails with all strategies.
        RuntimeError: If pandas is not installed.
    """
    pd = _require_pandas('Parquet reading')

    engines_to_try = ['pyarrow', 'fastparquet']
    last_error: Exception | None = None

    for engine in engines_to_try:
        try:
            df = pd.read_parquet(file_path, engine=engine)
            logger.debug(
                'Read Parquet file with engine %s, shape: %s', engine, df.shape
            )
            result: str = df.to_string(index=False)
            return result
        except (ValueError, OSError) as e:
            last_error = e
            logger.debug(
                'Failed to read Parquet with engine %s: %s', engine, e
            )
            continue

    raise FileReadException(
        str(file_path),
        f'Failed to read Parquet file with any engine. Last error: {last_error}',
    ) from last_error
