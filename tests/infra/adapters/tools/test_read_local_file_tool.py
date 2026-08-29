import contextlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from createagents.infra.adapters.tools.read_local_file_tool import (
    read_local_file_tool as tool_mod,
)
from createagents.infra.adapters.tools.read_local_file_tool.read_local_file_tool import (
    ReadLocalFileTool,
)


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


@pytest.mark.unit
class TestReadLocalFileTool:
    @pytest.fixture(autouse=True)
    def allow_temp_directory(self, monkeypatch):
        monkeypatch.setenv('FILE_TOOL_BASE_DIR', '/')

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
        assert 'type' in tool.parameters
        assert tool.parameters['type'] == 'object'
        assert 'properties' in tool.parameters
        assert 'path' in tool.parameters['properties']
        assert 'max_tokens' in tool.parameters['properties']
        assert 'required' in tool.parameters
        assert 'path' in tool.parameters['required']

    # assertion-reduction-reason: public tool behavior replaces private checks.
    def test_max_file_size_constant_defined(self):
        tool = ReadLocalFileTool()
        assert tool.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024

    def test_execute_read_simple_text_file(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('Hello, World!')
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert 'Hello, World!' in result
        finally:
            Path(filepath).unlink()

    def test_execute_file_not_found(self):
        tool = ReadLocalFileTool()

        result = tool.execute(path='/nonexistent/file.txt', max_tokens=1000)

        assert result.startswith('[ReadLocalFileTool Error]')
        assert 'File not found' in result

    def test_execute_path_is_directory(self):
        tool = ReadLocalFileTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute(path=tmpdir, max_tokens=1000)

            assert result.startswith('[ReadLocalFileTool Error]')
            assert 'directory' in result.lower()

    def test_execute_file_too_large(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='wb', suffix='.txt', delete=False
        ) as f:
            large_data = b'x' * (tool.MAX_FILE_SIZE_BYTES + 1024)
            f.write(large_data)
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=100000)

            assert result.startswith('[ReadLocalFileTool Error]')
            assert 'File too large' in result
        finally:
            Path(filepath).unlink()

    def test_execute_content_exceeds_token_limit(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            large_text = 'word ' * 10000
            f.write(large_text)
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=100)

            assert result.startswith('[ReadLocalFileTool Error]')
            assert 'exceeds token limit' in result
        finally:
            Path(filepath).unlink()

    def test_execute_with_default_max_tokens(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('Test content')
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=30000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert 'Test content' in result
        finally:
            Path(filepath).unlink()

    def test_execute_resolves_relative_path(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('Content')
            f.flush()
            filepath = f.name

        try:
            filename = Path(filepath).name
            result = tool.execute(path=filename, max_tokens=1000)

            assert result.startswith('[ReadLocalFileTool Error]')
        finally:
            Path(filepath).unlink()

    def test_execute_logs_operation(self, caplog):
        import logging

        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('Test content')
            f.flush()
            filepath = f.name

        try:
            with caplog.at_level(logging.INFO):
                tool.execute(path=filepath, max_tokens=1000)

            assert any(
                'Successfully read file' in r.message for r in caplog.records
            )
        finally:
            Path(filepath).unlink()

    def test_execute_handles_permission_error(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('Test')
            f.flush()
            filepath = f.name

        try:
            Path(filepath).chmod(0o000)

            result = tool.execute(path=filepath, max_tokens=1000)

            assert result.startswith('[ReadLocalFileTool Error]')
            assert 'Permission denied' in result or 'File not found' in result
        finally:
            with contextlib.suppress(OSError):
                Path(filepath).chmod(0o644)
                Path(filepath).unlink()

    def test_execute_with_python_file(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("def hello():\n    return 'world'")
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert 'def hello()' in result
        finally:
            Path(filepath).unlink()

    def test_execute_with_markdown_file(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False
        ) as f:
            f.write('# Header\n\nParagraph')
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert '# Header' in result
        finally:
            Path(filepath).unlink()

    def test_execute_with_json_file(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            f.write('{"key": "value"}')
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert 'key' in result
            assert 'value' in result
        finally:
            Path(filepath).unlink()

    def test_execute_counts_tokens_correctly(self, caplog):
        import logging

        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write('This is a test ' * 100)
            f.flush()
            filepath = f.name

        try:
            with caplog.at_level(logging.DEBUG):
                tool.execute(path=filepath, max_tokens=10000)

            assert any('tokens' in r.message for r in caplog.records)
        finally:
            Path(filepath).unlink()

    def test_execute_with_empty_file(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert result == '' or len(result) == 0
        finally:
            Path(filepath).unlink()

    def test_execute_detects_file_type_correctly(self, caplog):
        import logging

        tool = ReadLocalFileTool()

        extensions = ['.txt', '.py', '.md', '.json', '.xml']

        for ext in extensions:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix=ext, delete=False
            ) as f:
                f.write('content')
                f.flush()
                filepath = f.name

            try:
                with caplog.at_level(logging.DEBUG):
                    tool.execute(path=filepath, max_tokens=1000)

                assert any('file as type' in r.message for r in caplog.records)
            finally:
                Path(filepath).unlink()

    def test_execute_handles_unexpected_exception(self):
        tool = ReadLocalFileTool()

        with patch(
            'pathlib.Path.resolve', side_effect=Exception('Unexpected')
        ):
            result = tool.execute(path='/some/path', max_tokens=1000)

            assert result.startswith('[ReadLocalFileTool Error]')
            assert 'Unexpected error' in result

    def test_parameters_schema_has_defaults(self):
        tool = ReadLocalFileTool()
        max_tokens_param = tool.parameters['properties']['max_tokens']

        assert 'default' in max_tokens_param
        assert max_tokens_param['default'] == 30000

    def test_tool_instantiation(self):
        tool = ReadLocalFileTool()
        assert tool.name == 'readlocalfile'
        assert isinstance(tool.description, str)
        assert tool.parameters is not None

    def test_tool_handles_unicode_content(self):
        tool = ReadLocalFileTool()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write('Café ☕ 日本語 🎉')
            f.flush()
            filepath = f.name

        try:
            result = tool.execute(path=filepath, max_tokens=1000)

            assert not result.startswith('[ReadLocalFileTool Error]')
            assert 'Café' in result or 'Caf' in result
        finally:
            Path(filepath).unlink()

    def test_multiple_executions_independent(self):
        tool = ReadLocalFileTool()

        files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.txt', delete=False
                ) as f:
                    f.write(f'Content {i}')
                    f.flush()
                    files.append(f.name)

            results = [tool.execute(path=f, max_tokens=1000) for f in files]

            assert all(
                not r.startswith('[ReadLocalFileTool Error]') for r in results
            )
            assert 'Content 0' in results[0]
            assert 'Content 1' in results[1]
            assert 'Content 2' in results[2]
        finally:
            for file_path in files:
                Path(file_path).unlink()

    def test_error_format_consistency(self):
        tool = ReadLocalFileTool()

        errors = [
            tool.execute(path='/nonexistent', max_tokens=1000),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            errors.append(tool.execute(path=tmpdir, max_tokens=1000))

        for error in errors:
            assert error.startswith('[ReadLocalFileTool Error]')
            assert ':' in error


@pytest.mark.unit
class TestReadLocalFileToolConstants:
    def test_tool_name_constant(self):
        assert ReadLocalFileTool.name == 'readlocalfile'

    def test_description_constant(self):
        assert isinstance(ReadLocalFileTool.description, str)
        assert len(ReadLocalFileTool.description) > 0

    def test_parameters_constant(self):
        assert isinstance(ReadLocalFileTool.parameters, dict)
        assert ReadLocalFileTool.parameters['type'] == 'object'

    def test_max_file_size_is_class_attribute(self):
        assert ReadLocalFileTool.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024


@pytest.mark.unit
class TestReadLocalFileToolMissingDependencies:
    def test_tool_instantiation_when_dependencies_available(self):
        tool = ReadLocalFileTool()
        assert tool is not None
        assert tool.name == 'readlocalfile'

    def test_tool_raises_helpful_error_when_dependencies_missing(
        self, monkeypatch
    ):
        monkeypatch.setattr(tool_mod, 'DEPENDENCIES_AVAILABLE', False)
        monkeypatch.setattr(
            tool_mod, 'IMPORT_ERROR', ImportError('No module named pandas')
        )

        with pytest.raises(
            RuntimeError,
            match='ReadLocalFileTool requires optional dependencies',
        ):
            tool_mod.ReadLocalFileTool()
