from pathlib import Path

from ....config import LoggingConfig
from .constants import COMMON_ENCODINGS

logger = LoggingConfig.get_logger(__name__)


def detect_encoding(file_path: Path) -> str:
    """Detect the encoding of a file using chardet.

    Args:
        file_path: Path to the file.

    Returns:
        Detected encoding name, or 'utf-8' as fallback.
    """
    try:
        import chardet

        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(100000)  # Read first 100KB for detection
                result = chardet.detect(raw_data)
                detected_encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)

                logger.debug(
                    'Detected encoding: %s (confidence: %.2f)',
                    detected_encoding,
                    confidence,
                )

                # If confidence is low, fallback to utf-8
                if confidence < 0.7:
                    logger.warning(
                        'Low confidence (%.2f) in detected encoding, '
                        'trying common encodings',
                        confidence,
                    )
                    return 'utf-8'

                return detected_encoding or 'utf-8'
        except (OSError, ValueError) as e:
            logger.warning('Encoding detection failed: %s, using utf-8', e)
            return 'utf-8'

    except ImportError:
        logger.warning(
            'chardet not available, using utf-8 as default encoding'
        )
        return 'utf-8'


def candidate_encodings(file_path: Path) -> list[str]:
    """List encodings to try for a file, best guess first.

    Args:
        file_path: Path to the file.

    Returns:
        Detected encoding followed by the remaining common encodings.
    """
    detected_encoding = detect_encoding(file_path)
    return [detected_encoding] + [
        enc for enc in COMMON_ENCODINGS if enc != detected_encoding
    ]


def read_text_file(file_path: Path) -> str:
    """Read a plain text file with automatic encoding detection.

    Args:
        file_path: Path to the text file.

    Returns:
        File content as string.

    Raises:
        UnicodeDecodeError: If file cannot be decoded with any supported encoding.
    """
    last_error: Exception | None = None
    for encoding in candidate_encodings(file_path):
        try:
            content = file_path.read_text(encoding=encoding, errors='strict')
            logger.debug('Successfully read file with encoding: %s', encoding)
            return content
        except (UnicodeDecodeError, LookupError) as e:
            last_error = e
            logger.debug('Failed to read with %s: %s', encoding, e)
            continue

    # If all encodings fail, try UTF-8 with error replacement
    try:
        content = file_path.read_text(encoding='utf-8', errors='replace')
        logger.warning(
            'All encodings failed, using UTF-8 with character replacement'
        )
        return content
    except (OSError, ValueError) as e:
        raise UnicodeDecodeError(
            'unknown', b'', 0, 0, f'Failed to decode file: {last_error}'
        ) from e
