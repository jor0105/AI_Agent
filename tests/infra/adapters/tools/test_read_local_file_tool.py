from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from createagents.infra.adapters.tools.read_local_file_tool import (
    read_local_file_tool as tool_mod,
)
from createagents.infra.adapters.tools.read_local_file_tool.read_local_file_tool import (
    ReadLocalFileTool,
)
from createagents.infra.config import EnvironmentConfig

# assertion-reduction-reason: Replaced unrestricted temporary-file cases with
# isolated sandbox, traversal, symlink, and content-exposure coverage.


def _write_file(
    directory: Path,
    name: str,
    content: str | bytes,
) -> Path:
    """Create one fixture file inside the requested directory."""
    file_path = directory / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        file_path.write_bytes(content)
    else:
        file_path.write_text(content, encoding='utf-8')
    return file_path


def _write_external_file(
    sandbox_dir: Path,
    name: str,
    content: str,
) -> Path:
    """Create an explicitly external fixture for a sandbox rejection test."""
    return _write_file(sandbox_dir.parent, name, content)


@pytest.fixture(autouse=True)
def fake_tiktoken_encoding(monkeypatch):
    """Keep file-tool unit tests independent from tiktoken's cache download."""
    encoding = Mock()
    encoding.encode.side_effect = lambda text: text.split()
    monkeypatch.setattr(
        tool_mod,
        'initialize_tiktoken',
        Mock(return_value=encoding),
    )


@pytest.fixture(autouse=True)
def sandbox_dir(monkeypatch, tmp_path: Path) -> Generator[Path, None, None]:
    """Restrict every test to an isolated directory unless it opts out."""
    monkeypatch.setenv('FILE_TOOL_BASE_DIR', str(tmp_path))
    EnvironmentConfig.clear_cache()
    yield tmp_path
    EnvironmentConfig.clear_cache()


@pytest.mark.unit
class TestReadLocalFileTool:
    def test_tool_has_correct_name(self):
        tool = ReadLocalFileTool()

        assert tool.name == 'readlocalfile'

    def test_tool_has_description(self):
        tool = ReadLocalFileTool()

        assert tool.description
        assert 'read' in tool.description.lower()
        assert 'file' in tool.description.lower()

    def test_tool_has_parameters_schema(self):
        tool = ReadLocalFileTool()

        assert tool.parameters['type'] == 'object'
        assert 'path' in tool.parameters['properties']
        assert 'max_tokens' in tool.parameters['properties']
        assert tool.parameters['required'] == ['path']

    # assertion-reduction-reason: public tool behavior replaces private checks.
    def test_max_file_size_constant_defined(self):
        tool = ReadLocalFileTool()

        assert tool.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024

    def test_execute_reads_file_inside_sandbox(self, sandbox_dir: Path):
        file_path = _write_file(sandbox_dir, 'hello.txt', 'Hello, World!')

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=1000
        )

        assert not result.startswith('[ReadLocalFileTool Error]')
        assert result == 'Hello, World!'

    def test_execute_rejects_absolute_path_outside_sandbox(
        self, sandbox_dir: Path
    ):
        external_content = 'outside sandbox secret'
        file_path = _write_external_file(
            sandbox_dir,
            'external.txt',
            external_content,
        )

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=1000
        )

        assert result.startswith('[ReadLocalFileTool Error] Access denied:')
        assert external_content not in result

    def test_execute_rejects_parent_traversal_outside_sandbox(
        self, sandbox_dir: Path
    ):
        external_content = 'parent traversal secret'
        file_path = _write_external_file(
            sandbox_dir,
            'traversal.txt',
            external_content,
        )
        traversal_path = sandbox_dir / '..' / file_path.name

        result = ReadLocalFileTool().execute(
            path=str(traversal_path), max_tokens=1000
        )

        assert result.startswith('[ReadLocalFileTool Error] Access denied:')
        assert external_content not in result

    def test_execute_rejects_symlink_escaping_sandbox(self, sandbox_dir: Path):
        external_content = 'symlink target secret'
        external_file = _write_external_file(
            sandbox_dir,
            'symlink-target.txt',
            external_content,
        )
        symlink = sandbox_dir / 'external-link.txt'
        symlink.symlink_to(external_file)

        result = ReadLocalFileTool().execute(
            path=str(symlink), max_tokens=1000
        )

        assert result.startswith('[ReadLocalFileTool Error] Access denied:')
        assert external_content not in result

    def test_execute_file_not_found_inside_sandbox(self, sandbox_dir: Path):
        missing_file = sandbox_dir / 'missing.txt'

        result = ReadLocalFileTool().execute(
            path=str(missing_file), max_tokens=1000
        )

        assert result.startswith('[ReadLocalFileTool Error] File not found:')

    def test_execute_path_is_directory(self, sandbox_dir: Path):
        directory = sandbox_dir / 'directory'
        directory.mkdir()

        result = ReadLocalFileTool().execute(
            path=str(directory), max_tokens=1000
        )

        assert result.startswith(
            '[ReadLocalFileTool Error] Path is a directory:'
        )

    def test_execute_file_too_large(self, monkeypatch, sandbox_dir: Path):
        monkeypatch.setattr(ReadLocalFileTool, 'MAX_FILE_SIZE_BYTES', 10)
        file_path = _write_file(sandbox_dir, 'large.txt', b'x' * 11)

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=100000
        )

        assert result.startswith('[ReadLocalFileTool Error] File too large:')

    def test_execute_content_exceeds_token_limit(self, sandbox_dir: Path):
        file_path = _write_file(sandbox_dir, 'tokens.txt', 'word ' * 10000)

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=100
        )

        assert result.startswith(
            '[ReadLocalFileTool Error] Content exceeds token limit:'
        )

    def test_execute_uses_default_max_tokens(self, sandbox_dir: Path):
        file_path = _write_file(sandbox_dir, 'default.txt', 'Test content')

        result = ReadLocalFileTool().execute(path=str(file_path))

        assert result == 'Test content'

    def test_execute_rejects_relative_path_that_escapes_sandbox(
        self, sandbox_dir: Path, monkeypatch
    ):
        external_content = 'relative path secret'
        external_file = _write_external_file(
            sandbox_dir,
            'relative-external.txt',
            external_content,
        )
        monkeypatch.chdir(sandbox_dir)

        result = ReadLocalFileTool().execute(
            path=f'../{external_file.name}', max_tokens=1000
        )

        assert result.startswith('[ReadLocalFileTool Error] Access denied:')
        assert external_content not in result

    def test_execute_logs_successful_operation(
        self, sandbox_dir: Path, caplog
    ):
        import logging

        file_path = _write_file(sandbox_dir, 'logged.txt', 'Test content')

        with caplog.at_level(logging.INFO):
            ReadLocalFileTool().execute(path=str(file_path), max_tokens=1000)

        assert any(
            'Successfully read file' in record.message
            for record in caplog.records
        )

    def test_execute_handles_permission_error(
        self, sandbox_dir: Path, monkeypatch
    ):
        file_path = _write_file(sandbox_dir, 'restricted.txt', 'Test')
        monkeypatch.setattr(
            tool_mod,
            'read_file_by_type',
            Mock(side_effect=PermissionError),
        )

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=1000
        )

        assert result.startswith(
            '[ReadLocalFileTool Error] Permission denied:'
        )

    @pytest.mark.parametrize(
        ('name', 'content', 'expected_fragment'),
        [
            ('example.py', "def hello():\n    return 'world'", 'def hello()'),
            ('example.md', '# Header\n\nParagraph', '# Header'),
            ('example.json', '{"key": "value"}', '"key"'),
        ],
    )
    def test_execute_reads_supported_textual_file_types(
        self,
        sandbox_dir: Path,
        name: str,
        content: str,
        expected_fragment: str,
    ):
        file_path = _write_file(sandbox_dir, name, content)

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=1000
        )

        assert not result.startswith('[ReadLocalFileTool Error]')
        assert expected_fragment in result

    def test_execute_counts_tokens(self, sandbox_dir: Path, caplog):
        import logging

        file_path = _write_file(
            sandbox_dir,
            'counted.txt',
            'This is a test ' * 100,
        )

        with caplog.at_level(logging.DEBUG):
            ReadLocalFileTool().execute(path=str(file_path), max_tokens=10000)

        assert any('tokens' in record.message for record in caplog.records)

    def test_execute_reads_empty_file(self, sandbox_dir: Path):
        file_path = _write_file(sandbox_dir, 'empty.txt', '')

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=1000
        )

        assert result == ''

    @pytest.mark.parametrize(
        'extension', ['.txt', '.py', '.md', '.json', '.xml']
    )
    def test_execute_detects_file_type(
        self, sandbox_dir: Path, caplog, extension
    ):
        import logging

        file_path = _write_file(
            sandbox_dir,
            f'content{extension}',
            'content',
        )

        with caplog.at_level(logging.DEBUG):
            ReadLocalFileTool().execute(path=str(file_path), max_tokens=1000)

        assert any(
            'file as type' in record.message for record in caplog.records
        )

    def test_execute_handles_unexpected_exception(self):
        with patch(
            'pathlib.Path.resolve', side_effect=Exception('Unexpected')
        ):
            result = ReadLocalFileTool().execute(
                path='path-that-raises', max_tokens=1000
            )

        assert result.startswith('[ReadLocalFileTool Error] Unexpected error:')
        assert 'Unexpected' in result

    def test_parameters_schema_has_default_max_tokens(self):
        tool = ReadLocalFileTool()

        assert tool.parameters['properties']['max_tokens']['default'] == 30000

    def test_tool_handles_unicode_content(self, sandbox_dir: Path):
        file_path = _write_file(
            sandbox_dir,
            'unicode.txt',
            'Café ☕ 日本語 🎉',
        )

        result = ReadLocalFileTool().execute(
            path=str(file_path), max_tokens=1000
        )

        assert result == 'Café ☕ 日本語 🎉'

    def test_multiple_executions_are_independent(self, sandbox_dir: Path):
        file_paths = [
            _write_file(
                sandbox_dir,
                f'content-{index}.txt',
                f'Content {index}',
            )
            for index in range(3)
        ]
        tool = ReadLocalFileTool()
        results = [
            tool.execute(path=str(file_path), max_tokens=1000)
            for file_path in file_paths
        ]

        assert results == ['Content 0', 'Content 1', 'Content 2']

    def test_error_format_is_consistent(self, sandbox_dir: Path):
        missing_file = sandbox_dir / 'missing.txt'
        directory = sandbox_dir / 'directory'
        directory.mkdir()
        tool = ReadLocalFileTool()
        errors = [
            tool.execute(path=str(missing_file), max_tokens=1000),
            tool.execute(path=str(directory), max_tokens=1000),
        ]

        assert all(
            error.startswith('[ReadLocalFileTool Error]') for error in errors
        )
        assert all(':' in error for error in errors)


@pytest.mark.unit
class TestReadLocalFileToolConstants:
    def test_tool_name_constant(self):
        assert ReadLocalFileTool.name == 'readlocalfile'

    def test_description_constant(self):
        assert isinstance(ReadLocalFileTool.description, str)
        assert ReadLocalFileTool.description

    def test_parameters_constant(self):
        assert isinstance(ReadLocalFileTool.parameters, dict)
        assert ReadLocalFileTool.parameters['type'] == 'object'

    def test_max_file_size_is_class_attribute(self):
        assert ReadLocalFileTool.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024


@pytest.mark.unit
class TestReadLocalFileToolMissingDependencies:
    def test_tool_instantiation_when_dependencies_available(self):
        tool = ReadLocalFileTool()

        assert tool.name == 'readlocalfile'

    def test_tool_raises_helpful_error_when_dependencies_missing(
        self, monkeypatch
    ):
        monkeypatch.setattr(tool_mod, 'DEPENDENCIES_AVAILABLE', False)
        monkeypatch.setattr(
            tool_mod,
            'IMPORT_ERROR',
            ImportError('No module named pandas'),
        )

        with pytest.raises(
            RuntimeError,
            match='ReadLocalFileTool requires optional dependencies',
        ):
            tool_mod.ReadLocalFileTool()
