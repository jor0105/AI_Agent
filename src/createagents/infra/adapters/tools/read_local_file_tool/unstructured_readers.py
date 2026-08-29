import io
import sys
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .....domain import FileReadException
from ....config import LoggingConfig

logger = LoggingConfig.get_logger(__name__)


def _partition_quietly(
    partition_fn: Callable[..., Any],
    file_path: Path,
    stderr_label: str,
    warning_label: str,
) -> Any:
    """Run an unstructured partitioner, muting known noisy warnings.

    Args:
        partition_fn: `unstructured` partition callable to invoke.
        file_path: Path to the file being parsed.
        stderr_label: Prefix used when logging captured stderr lines.
        warning_label: Label used when logging captured Python warnings.

    Returns:
        The elements returned by the partitioner.

    """
    # Redirect stderr to capture warnings from C libraries
    stderr_capture = io.StringIO()
    old_stderr = sys.stderr

    try:
        sys.stderr = stderr_capture

        with warnings.catch_warnings(record=True) as w:
            # Suppress specific deprecation warnings from dependencies FIRST
            warnings.filterwarnings(
                'ignore', message='.*max_size.*deprecated.*'
            )
            warnings.filterwarnings(
                'ignore',
                category=DeprecationWarning,
                module='.*unstructured.*',
            )
            # Then enable all other warnings
            warnings.simplefilter('always')

            elements = partition_fn(
                filename=str(file_path),
                # Auto chooses best strategy (fast, hi_res, ocr)
                strategy='auto',
                infer_table_structure=True,  # Extract tables as structured data
                languages=['eng'],  # Suppress "No languages specified" warning
            )

        # Restore stderr
        sys.stderr = old_stderr

        # Log stderr warnings that aren't about max_size
        stderr_output = stderr_capture.getvalue()
        if stderr_output:
            for line in stderr_output.strip().split('\n'):
                if line and 'max_size' not in line.lower():
                    logger.warning(
                        '%s processing stderr: %s', stderr_label, line
                    )

        # Log any Python warnings that weren't filtered
        for warning in w:
            if 'max_size' not in str(warning.message).lower():
                logger.warning(
                    'Warning during %s processing: %s',
                    warning_label,
                    warning.message,
                )
    finally:
        # Ensure stderr is always restored
        sys.stderr = old_stderr

    return elements


def _group_pdf_elements_by_page(elements: Any) -> list[str]:
    """Group extracted PDF elements into per-page text blocks.

    Args:
        elements: Elements returned by `partition_pdf`.

    Returns:
        Text blocks, one per page when page metadata is available.

    """
    content_parts: list[str] = []
    current_page = None
    page_content: list[str] = []

    for element in elements:
        # Group content by page if metadata is available
        element_page = (
            getattr(element.metadata, 'page_number', None)
            if hasattr(element, 'metadata')
            else None
        )

        if element_page is not None and element_page != current_page:
            # Save previous page content
            if page_content:
                content_parts.append(
                    f'--- Page {current_page} ---\n' + '\n'.join(page_content)
                )
                page_content = []
            current_page = element_page

        element_text = str(element).strip()
        if element_text:
            page_content.append(element_text)

    # Add last page
    if page_content:
        if current_page is not None:
            content_parts.append(
                f'--- Page {current_page} ---\n' + '\n'.join(page_content)
            )
        else:
            content_parts.extend(page_content)

    return content_parts


def read_pdf_file(file_path: Path) -> str:
    """Read a PDF file and extract text from all pages with error handling.

    Uses unstructured library for robust PDF parsing that handles various formats,
    including scanned PDFs with OCR capabilities. Supports additional
    document types beyond basic PDFs.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text from all PDF pages.

    Raises:
        FileReadException: If PDF reading fails.
        RuntimeError: If unstructured is not installed.

    """
    try:
        from unstructured.partition.pdf import (
            partition_pdf,
        )
    except ImportError as e:
        raise RuntimeError(
            'unstructured is required for PDF reading. '
            'Install with: pip install createagents[file-tools]'
        ) from e

    try:
        logger.debug('Reading PDF file: %s', file_path)

        # partition_pdf automatically handles:
        # - Text extraction from native PDFs
        # - OCR for scanned PDFs (if pytesseract is available)
        # - Layout detection and element classification
        # - Tables, images, and other structured content
        elements = _partition_quietly(partition_pdf, file_path, 'PDF', 'PDF')

        if not elements:
            raise FileReadException(
                str(file_path), 'No readable content found in PDF'
            )

        result = '\n\n'.join(_group_pdf_elements_by_page(elements))
        logger.debug(
            'Successfully extracted %s elements from PDF', len(elements)
        )
        return result

    except FileReadException:
        raise
    except (ValueError, OSError, RuntimeError) as e:
        raise FileReadException(
            str(file_path),
            f'PDF processing failed: {type(e).__name__}: {e}',
        ) from e
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f'PDF processing failed: {type(e).__name__}: {e}',
        ) from e


def read_document_file(file_path: Path) -> str:
    """Read various document formats using unstructured library.

    Supports Word documents (.doc, .docx), PowerPoint (.ppt, .pptx),
    OpenDocument (.odt), EPUB, MSG, RTF, and other formats.

    Args:
        file_path: Path to the document file.

    Returns:
        Extracted text from the document.

    Raises:
        FileReadException: If document reading fails.
        RuntimeError: If unstructured is not installed.

    """
    try:
        from unstructured.partition.auto import (
            partition,
        )
    except ImportError as e:
        raise RuntimeError(
            'unstructured is required for document reading. '
            'Install with: pip install createagents[file-tools]'
        ) from e

    try:
        logger.debug('Reading document file: %s', file_path)

        # partition automatically detects file type and uses appropriate parser
        elements = _partition_quietly(
            partition, file_path, 'Document', 'document'
        )

        if not elements:
            raise FileReadException(
                str(file_path), 'No readable content found in document'
            )

        content_parts = [
            str(element).strip()
            for element in elements
            if str(element).strip()
        ]

        result = '\n\n'.join(content_parts)
        logger.debug(
            'Successfully extracted %s elements from document', len(elements)
        )
        return result

    except FileReadException:
        raise
    except (ValueError, OSError, RuntimeError) as e:
        raise FileReadException(
            str(file_path),
            f'Document processing failed: {type(e).__name__}: {e}',
        ) from e
    except Exception as e:
        raise FileReadException(
            str(file_path),
            f'Document processing failed: {type(e).__name__}: {e}',
        ) from e
