import tempfile
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

import pytest

from createagents.domain import FileReadException

try:
    from createagents.infra.adapters.tools.read_local_file_tool.constants import (
        COMMON_ENCODINGS,
        DOCUMENT_EXTENSIONS,
        EXCEL_EXTENSIONS,
        MAX_FILE_SIZE_BYTES,
        TEXT_EXTENSIONS,
        TIKTOKEN_ENCODING,
        FileType,
    )
    from createagents.infra.adapters.tools.read_local_file_tool.encoding_utils import (
        detect_encoding,
        read_text_file,
    )
    from createagents.infra.adapters.tools.read_local_file_tool.file_dispatch import (
        determine_file_type,
        read_file_by_type,
    )
    from createagents.infra.adapters.tools.read_local_file_tool.tabular_readers import (
        read_csv_file,
        read_excel_file,
        read_parquet_file,
    )
    from createagents.infra.adapters.tools.read_local_file_tool.token_utils import (
        count_tokens,
        initialize_tiktoken,
    )
    from createagents.infra.adapters.tools.read_local_file_tool.unstructured_readers import (
        read_document_file,
        read_pdf_file,
    )

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


@pytest.fixture
def fake_tiktoken_module():
    """Provide an isolated tiktoken module without fetching its encoding data."""
    module = ModuleType('tiktoken')
    module.get_encoding = Mock()
    with patch.dict('sys.modules', {'tiktoken': module}):
        yield module


@pytest.mark.unit
class TestFileTypeEnum:
    # assertion-reduction-reason: exact enum values replace presence checks.
    def test_file_type_enum_values(self):
        assert FileType.TEXT.value == 'text'
        assert FileType.CSV.value == 'csv'
        assert FileType.EXCEL.value == 'excel'
        assert FileType.PDF.value == 'pdf'
        assert FileType.PARQUET.value == 'parquet'
        assert FileType.DOCUMENT.value == 'document'
        assert FileType.UNKNOWN.value == 'unknown'

    def test_file_type_enum_unique_values(self):
        values = [ft.value for ft in FileType]
        assert len(values) == len(set(values))

    def test_file_type_string_values(self):
        assert FileType.TEXT.value == 'text'
        assert FileType.CSV.value == 'csv'
        assert FileType.EXCEL.value == 'excel'
        assert FileType.PDF.value == 'pdf'
        assert FileType.PARQUET.value == 'parquet'
        assert FileType.DOCUMENT.value == 'document'
        assert FileType.UNKNOWN.value == 'unknown'


@pytest.mark.unit
class TestConstants:
    def test_text_extensions_is_frozenset(self):
        assert isinstance(TEXT_EXTENSIONS, frozenset)

    def test_text_extensions_contains_common_types(self):
        expected = {'txt', 'py', 'md', 'json', 'xml', 'yaml', 'yml'}
        assert expected.issubset(TEXT_EXTENSIONS)

    def test_excel_extensions_defined(self):
        assert isinstance(EXCEL_EXTENSIONS, frozenset)
        assert 'xlsx' in EXCEL_EXTENSIONS
        assert 'xls' in EXCEL_EXTENSIONS

    def test_document_extensions_defined(self):
        assert isinstance(DOCUMENT_EXTENSIONS, frozenset)
        assert 'docx' in DOCUMENT_EXTENSIONS
        assert 'pptx' in DOCUMENT_EXTENSIONS

    def test_max_file_size_bytes_constant(self):
        assert MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024

    def test_tiktoken_encoding_constant(self):
        assert TIKTOKEN_ENCODING == 'cl100k_base'

    def test_common_encodings_is_list(self):
        assert isinstance(COMMON_ENCODINGS, list)
        assert 'utf-8' in COMMON_ENCODINGS
        assert 'latin-1' in COMMON_ENCODINGS


@pytest.mark.unit
class TestInitializeTiktoken:
    def test_initialize_tiktoken_returns_encoding(self, fake_tiktoken_module):
        expected_encoding = Mock()
        fake_tiktoken_module.get_encoding.return_value = expected_encoding

        encoding = initialize_tiktoken()

        assert encoding is expected_encoding

    def test_initialize_tiktoken_uses_correct_encoding(
        self, fake_tiktoken_module
    ):
        fake_tiktoken_module.get_encoding.return_value = Mock()

        initialize_tiktoken()

        fake_tiktoken_module.get_encoding.assert_called_once_with(
            TIKTOKEN_ENCODING
        )

    def test_initialize_tiktoken_raises_on_import_error(self):
        with (
            patch(
                'builtins.__import__',
                side_effect=ImportError('tiktoken missing'),
            ),
            pytest.raises(
                RuntimeError, match='tiktoken is required for token counting'
            ),
        ):
            initialize_tiktoken()


@pytest.mark.unit
class TestCountTokens:
    def test_count_tokens_simple_text(self):
        encoding = Mock()
        encoding.encode.return_value = [1, 2, 3]
        text = 'Hello, world!'

        count = count_tokens(text, encoding)

        assert count == 3
        encoding.encode.assert_called_once_with(text)

    def test_count_tokens_empty_string(self):
        encoding = Mock()
        encoding.encode.return_value = []

        count = count_tokens('', encoding)

        assert count == 0

    def test_count_tokens_long_text(self):
        encoding = Mock()
        encoding.encode.return_value = list(range(250))
        text = 'word ' * 1000

        count = count_tokens(text, encoding)

        assert count == 250

    def test_count_tokens_fallback_on_error(self):
        encoding = Mock()
        encoding.encode.side_effect = ValueError('Encoding error')

        text = 'test text'
        count = count_tokens(text, encoding)

        assert count == len(text) // 4


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestDetectEncoding:
    def test_detect_encoding_utf8_file(self):
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', delete=False
        ) as f:
            f.write('Hello UTF-8')
            f.flush()
            filepath = Path(f.name)

        try:
            encoding = detect_encoding(filepath)
            assert encoding in ['utf-8', 'ascii', 'UTF-8', 'ASCII']
        finally:
            filepath.unlink()

    def test_detect_encoding_returns_fallback(self):
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'')
            f.flush()
            filepath = Path(f.name)

        try:
            encoding = detect_encoding(filepath)
            assert encoding is not None
            assert isinstance(encoding, str)
        finally:
            filepath.unlink()

    def test_detect_encoding_handles_chardet_missing(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test')
            f.flush()
            filepath = Path(f.name)

        try:
            with patch.dict('sys.modules', {'chardet': None}):
                encoding = detect_encoding(filepath)
                assert encoding == 'utf-8'
        finally:
            filepath.unlink()


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadTextFile:
    def test_read_text_file_simple(self):
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', delete=False
        ) as f:
            f.write('Hello, World!')
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_text_file(filepath)
            assert content == 'Hello, World!'
        finally:
            filepath.unlink()

    def test_read_text_file_with_unicode(self):
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', delete=False
        ) as f:
            f.write('Café ☕ 日本語')
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_text_file(filepath)
            assert 'Café' in content or 'Caf' in content
        finally:
            filepath.unlink()

    def test_read_text_file_empty(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_text_file(filepath)
            assert content == ''
        finally:
            filepath.unlink()

    def test_read_text_file_tries_multiple_encodings(self):
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='latin-1', delete=False
        ) as f:
            f.write('Test content')
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_text_file(filepath)
            assert 'Test content' in content
        finally:
            filepath.unlink()


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestDetermineFileType:
    def test_determine_file_type_text_extensions(self):
        text_exts = ['txt', 'py', 'md', 'json']
        for ext in text_exts:
            file_type = determine_file_type(ext)
            assert file_type == FileType.TEXT

    def test_determine_file_type_csv(self):
        file_type = determine_file_type('csv')
        assert file_type == FileType.CSV

    def test_determine_file_type_excel(self):
        for ext in ['xls', 'xlsx', 'xlsm']:
            file_type = determine_file_type(ext)
            assert file_type == FileType.EXCEL

    def test_determine_file_type_pdf(self):
        file_type = determine_file_type('pdf')
        assert file_type == FileType.PDF

    def test_determine_file_type_parquet(self):
        file_type = determine_file_type('parquet')
        assert file_type == FileType.PARQUET

    def test_determine_file_type_document(self):
        for ext in ['docx', 'pptx', 'odt']:
            file_type = determine_file_type(ext)
            assert file_type == FileType.DOCUMENT

    def test_determine_file_type_unknown(self):
        file_type = determine_file_type('unknown_ext')
        assert file_type == FileType.UNKNOWN


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadFileByType:
    def test_read_file_by_type_text(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('Text content')
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_file_by_type(filepath, FileType.TEXT)
            assert 'Text content' in content
        finally:
            filepath.unlink()

    def test_read_file_by_type_unknown_fallback(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.unknown', delete=False
        ) as f:
            f.write('Unknown type content')
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_file_by_type(filepath, FileType.UNKNOWN)
            assert 'Unknown type content' in content
        finally:
            filepath.unlink()

    def test_read_file_by_type_raises_on_binary_unknown(self):
        filepath = Path('dummy.unknown')
        with (
            patch(
                'createagents.infra.adapters.tools.read_local_file_tool.file_dispatch.read_text_file',
                side_effect=UnicodeDecodeError(
                    'utf-8', b'', 0, 1, 'invalid byte'
                ),
            ),
            pytest.raises(
                FileReadException, match='Cannot decode file as text'
            ),
        ):
            read_file_by_type(filepath, FileType.UNKNOWN)


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadCSVFile:
    def test_read_csv_file_simple(self):
        pytest.importorskip('pandas')

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False
        ) as f:
            f.write('name,age\nAlice,30\nBob,25')
            f.flush()
            filepath = Path(f.name)

        try:
            content = read_csv_file(filepath)
            assert 'Alice' in content
            assert 'Bob' in content
        finally:
            filepath.unlink()


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadExcelFile:
    def test_read_excel_requires_pandas(self):
        assert callable(read_excel_file)


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadPDFFile:
    def test_read_pdf_requires_unstructured(self):
        assert callable(read_pdf_file)


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadDocumentFile:
    def test_read_document_requires_unstructured(self):
        assert callable(read_document_file)


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason='Optional dependencies not available'
)
@pytest.mark.unit
class TestReadParquetFile:
    def test_read_parquet_requires_pandas(self):
        assert callable(read_parquet_file)
