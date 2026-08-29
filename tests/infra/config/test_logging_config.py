import json
import logging
import os
import tempfile
from pathlib import Path
from typing import cast

from createagents.infra import (
    JSONFormatter,
    LoggingConfig,
    SensitiveDataFilter,
    SensitiveDataFormatter,
)


class TestSensitiveDataFormatter:
    def setup_method(self):
        SensitiveDataFilter.clear_cache()

    def test_format_filters_sensitive_data(self):
        formatter = SensitiveDataFormatter('%(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='password=secret123',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert 'secret123' not in result
        assert '[PASSWORD_REDACTED]' in result

    def test_format_preserves_normal_messages(self):
        formatter = SensitiveDataFormatter('%(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Normal message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert result == 'Normal message'

    def test_format_with_timestamp(self):
        formatter = SensitiveDataFormatter('%(asctime)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert 'Test message' in result
        assert '-' in result


class TestJSONFormatter:
    def setup_method(self):
        SensitiveDataFilter.clear_cache()

    def test_format_returns_valid_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test.module',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed['level'] == 'INFO'
        assert parsed['logger'] == 'test.module'
        assert parsed['message'] == 'Test message'
        assert parsed['module'] == 'test'
        assert parsed['line'] == 42

    def test_format_filters_sensitive_data_in_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='API_KEY=sk-123456789012',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert 'sk-123456789012' not in parsed['message']
        assert '[API_KEY_REDACTED]' in parsed['message']

    def test_format_includes_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError('Test error')
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error occurred',
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert 'exception' in parsed
        assert 'ValueError: Test error' in parsed['exception']


class TestLoggingConfig:
    def setup_method(self):
        LoggingConfig.reset()

    def teardown_method(self):
        LoggingConfig.reset()
        for key in [
            'LOG_LEVEL',
            'LOG_TO_FILE',
            'LOG_FILE_PATH',
            'LOG_JSON_FORMAT',
        ]:
            if key in os.environ:
                del os.environ[key]

    def test_configure_default_settings(self):
        LoggingConfig.configure()

        assert LoggingConfig._configured is True
        assert LoggingConfig._log_level == logging.INFO
        assert len(LoggingConfig._handlers) == 1

    def test_configure_custom_level(self):
        LoggingConfig.configure(level=logging.DEBUG)

        assert LoggingConfig._log_level == logging.DEBUG
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_from_env_var(self):
        os.environ['LOG_LEVEL'] = 'WARNING'
        LoggingConfig.configure()

        assert LoggingConfig._log_level == logging.WARNING

    def test_configure_invalid_env_var_uses_default(self):
        os.environ['LOG_LEVEL'] = 'INVALID'
        LoggingConfig.configure()

        assert LoggingConfig._log_level == logging.INFO

    def test_configure_with_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            assert len(LoggingConfig._handlers) == 2
            assert log_file.exists() or log_file.parent.exists()

    def test_configure_creates_log_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'nested' / 'dir' / 'test.log'

            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            assert log_file.parent.exists()

    def test_configure_with_json_format(self):
        LoggingConfig.configure(json_format=True)

        handlers = LoggingConfig.get_handlers()
        assert len(handlers) > 0
        assert isinstance(handlers[0].formatter, JSONFormatter)

    def test_configure_can_reconfigure(self):
        LoggingConfig.configure(level=logging.DEBUG)
        first_level = LoggingConfig._log_level
        assert first_level == logging.DEBUG

        LoggingConfig.configure(level=logging.ERROR)
        second_level = LoggingConfig._log_level

        # After source code changes, configure can now be called multiple times
        # Each call reconfigures the logging system
        assert second_level == logging.ERROR

    def test_get_logger_returns_logger(self):
        logger = LoggingConfig.get_logger('test.module')

        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test.module'

    def test_get_logger_does_not_configure_automatically(self):
        assert LoggingConfig._configured is False

        logger = LoggingConfig.get_logger('test')

        # Should NOT configure automatically anymore
        assert LoggingConfig._configured is False
        assert isinstance(logger, logging.Logger)

    def test_set_level_changes_level(self):
        LoggingConfig.configure(level=logging.INFO)

        LoggingConfig.set_level(logging.ERROR)

        assert LoggingConfig._log_level == logging.ERROR
        assert logging.getLogger().level == logging.ERROR

    def test_reset_clears_configuration(self):
        LoggingConfig.configure()
        assert LoggingConfig._configured is True

        LoggingConfig.reset()

        assert LoggingConfig._configured is False
        assert len(LoggingConfig._handlers) == 0

    def test_reset_clears_sensitive_data_cache(self):
        test_text = 'password=secret123'
        SensitiveDataFilter.filter(test_text)
        SensitiveDataFilter.filter(test_text)

        cache_info_before = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info_before.hits > 0 or cache_info_before.currsize > 0

        LoggingConfig.reset()

        cache_info_after = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info_after.currsize == 0
        assert cache_info_after.hits == 0
        assert cache_info_after.misses == 0

    def test_get_handlers_returns_copy(self):
        LoggingConfig.configure()
        handlers = LoggingConfig.get_handlers()

        handlers.clear()

        assert len(LoggingConfig._handlers) > 0

    def test_logging_filters_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            logger = LoggingConfig.get_logger('test')
            logger.info('User password=secret123')

            for handler in LoggingConfig._handlers:
                handler.flush()

            if log_file.exists():
                content = log_file.read_text()
                assert 'secret123' not in content
                assert '[PASSWORD_REDACTED]' in content

    def test_configure_with_env_file_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'app.log'
            os.environ['LOG_TO_FILE'] = 'true'
            os.environ['LOG_FILE_PATH'] = str(log_file)

            LoggingConfig.configure()

            assert len(LoggingConfig._handlers) == 2

    def test_configure_without_timestamp(self):
        LoggingConfig.configure(include_timestamp=False)

        handlers = LoggingConfig.get_handlers()
        formatter = handlers[0].formatter
        assert formatter is not None
        assert formatter._fmt is not None
        assert 'asctime' not in formatter._fmt

    def test_configure_custom_format_string(self):
        custom_format = '%(levelname)s - %(message)s'
        LoggingConfig.configure(format_string=custom_format)

        handlers = LoggingConfig.get_handlers()
        formatter = handlers[0].formatter
        assert formatter is not None
        assert formatter._fmt == custom_format

    def test_file_rotation_settings(self):
        from logging.handlers import RotatingFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            max_bytes = 1024
            backup_count = 3

            LoggingConfig.configure(
                log_to_file=True,
                log_file_path=str(log_file),
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

            handlers = LoggingConfig.get_handlers()
            file_handler = next(
                h for h in handlers if isinstance(h, RotatingFileHandler)
            )

            assert file_handler.maxBytes == max_bytes
            assert file_handler.backupCount == backup_count

    def test_multiple_loggers_share_config(self):
        LoggingConfig.configure(level=logging.WARNING)

        logger1 = LoggingConfig.get_logger('module1')
        logger2 = LoggingConfig.get_logger('module2')

        assert logger1.getEffectiveLevel() == logging.WARNING
        assert logger2.getEffectiveLevel() == logging.WARNING

    def test_logger_logs_at_correct_level(self):
        import io

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.WARNING)

        LoggingConfig.reset()
        LoggingConfig.configure(level=logging.WARNING)
        logger = LoggingConfig.get_logger('test')

        logger.addHandler(handler)

        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')

        handler.flush()
        output = stream.getvalue()

        assert 'Debug message' not in output
        assert 'Info message' not in output
        assert 'Warning message' in output


class TestLoggingIntegration:
    def setup_method(self):
        LoggingConfig.reset()

    def teardown_method(self):
        LoggingConfig.reset()

    def test_real_world_scenario_with_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'app.log'
            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            logger = LoggingConfig.get_logger('app')

            logger.info('User logged in: user@example.com')
            logger.debug('API request with key: sk-proj-123456789012')
            logger.warning(
                'Database connection: postgres://admin:pass123@db.com'
            )
            logger.error('Failed payment for card: 4532-1234-5678-9010')

            for handler in LoggingConfig._handlers:
                handler.flush()

            content = log_file.read_text()

            assert 'user@example.com' not in content
            assert 'sk-proj-123456789012' not in content
            assert 'pass123' not in content
            assert '4532-1234-5678-9010' not in content

            assert '[EMAIL_REDACTED]' in content
            assert (
                '[PASSWORD_REDACTED]' in content
                or '[CREDENTIALS_REDACTED]' in content
            )
            assert '[CREDIT_CARD_REDACTED]' in content

    def test_json_logging_production_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'app.json'
            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file), json_format=True
            )

            logger = LoggingConfig.get_logger('api')
            logger.info('Request received from user@test.com')

            for handler in LoggingConfig._handlers:
                handler.flush()

            lines = log_file.read_text().strip().split('\n')
            for line in lines:
                log_entry = json.loads(line)

                assert 'timestamp' in log_entry
                assert 'level' in log_entry
                assert 'logger' in log_entry
                assert 'message' in log_entry

                assert 'user@test.com' not in log_entry['message']

    def test_default_constants_defined(self):
        assert LoggingConfig.DEFAULT_LOG_LEVEL == logging.INFO
        assert LoggingConfig.DEFAULT_MAX_BYTES == 10 * 1024 * 1024
        assert LoggingConfig.DEFAULT_BACKUP_COUNT == 5
        assert LoggingConfig.DEFAULT_LOG_PATH == 'logs/app.log'

    def test_default_log_level_constant(self):
        assert LoggingConfig.DEFAULT_LOG_LEVEL == logging.INFO

    def test_default_max_bytes_constant(self):
        assert LoggingConfig.DEFAULT_MAX_BYTES == 10 * 1024 * 1024

    def test_default_backup_count_constant(self):
        assert LoggingConfig.DEFAULT_BACKUP_COUNT == 5

    def test_default_log_path_constant(self):
        assert LoggingConfig.DEFAULT_LOG_PATH == 'logs/app.log'

    def test_configure_uses_default_constants(self):
        LoggingConfig.configure()

        assert LoggingConfig._log_level == LoggingConfig.DEFAULT_LOG_LEVEL

    def test_resolve_log_file_path_with_none(self):
        result = LoggingConfig._resolve_log_file_path(None)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_resolve_log_file_path_with_valid_string(self, tmp_path):
        test_path = str(tmp_path / 'test.log')
        result = LoggingConfig._resolve_log_file_path(test_path)

        assert result == test_path

    def test_resolve_log_file_path_with_bool(self):
        result = LoggingConfig._resolve_log_file_path(cast(str, True))

        assert isinstance(result, str)
        assert result != 'True'

    def test_resolve_log_file_path_with_invalid_type(self):
        result = LoggingConfig._resolve_log_file_path(cast(str, 12345))

        assert isinstance(result, str)

    def test_resolve_log_file_path_respects_env_var(self):
        custom_path = '/custom/path/app.log'
        os.environ['LOG_FILE_PATH'] = custom_path

        try:
            result = LoggingConfig._resolve_log_file_path(None)
            assert result == custom_path
        finally:
            if 'LOG_FILE_PATH' in os.environ:
                del os.environ['LOG_FILE_PATH']

    def test_configure_with_custom_max_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            custom_max_bytes = 5 * 1024 * 1024
            LoggingConfig.configure(
                log_to_file=True,
                log_file_path=str(log_file),
                max_bytes=custom_max_bytes,
            )

            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert file_handlers[0].maxBytes == custom_max_bytes

    def test_configure_with_custom_backup_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            custom_backup = 3
            LoggingConfig.configure(
                log_to_file=True,
                log_file_path=str(log_file),
                backup_count=custom_backup,
            )

            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert file_handlers[0].backupCount == custom_backup

    def test_configure_uses_default_max_bytes_when_not_specified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert file_handlers[0].maxBytes == LoggingConfig.DEFAULT_MAX_BYTES

    def test_configure_uses_default_backup_count_when_not_specified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert (
                file_handlers[0].backupCount
                == LoggingConfig.DEFAULT_BACKUP_COUNT
            )

    def test_constants_are_immutable_values(self):
        assert isinstance(LoggingConfig.DEFAULT_LOG_LEVEL, int)
        assert isinstance(LoggingConfig.DEFAULT_MAX_BYTES, int)
        assert isinstance(LoggingConfig.DEFAULT_BACKUP_COUNT, int)
        assert isinstance(LoggingConfig.DEFAULT_LOG_PATH, str)

    def test_resolve_log_file_path_handles_path_like_objects(self, tmp_path):
        from pathlib import Path

        test_path = Path(tmp_path / 'test.log')
        result = LoggingConfig._resolve_log_file_path(str(test_path))

        assert result == str(test_path)

    def test_configure_with_default_log_path_creates_directory(self):
        if Path('logs').exists():
            LoggingConfig.configure(log_to_file=True)
            assert LoggingConfig._configured

    def test_magic_numbers_replaced_by_constants(self):
        assert LoggingConfig.DEFAULT_MAX_BYTES > 0
        assert LoggingConfig.DEFAULT_BACKUP_COUNT > 0
        assert len(LoggingConfig.DEFAULT_LOG_PATH) > 0

        assert LoggingConfig.DEFAULT_MAX_BYTES == 10485760
        assert LoggingConfig.DEFAULT_BACKUP_COUNT == 5

    def test_resolve_log_file_path_is_classmethod(self):
        import inspect

        assert inspect.ismethod(LoggingConfig._resolve_log_file_path)

    def test_constants_accessible_without_instantiation(self):
        level = LoggingConfig.DEFAULT_LOG_LEVEL
        max_bytes = LoggingConfig.DEFAULT_MAX_BYTES
        backup = LoggingConfig.DEFAULT_BACKUP_COUNT
        path = LoggingConfig.DEFAULT_LOG_PATH

        assert level is not None
        assert max_bytes is not None
        assert backup is not None
        assert path is not None

    def test_resolve_log_file_path_with_exception_handling(self):
        class UnconvertibleObject:
            def __str__(self) -> str:
                raise ValueError('Cannot convert to string')

        result = LoggingConfig._resolve_log_file_path(
            cast(str, UnconvertibleObject())
        )

        assert isinstance(result, str)
        assert result == LoggingConfig.DEFAULT_LOG_PATH or result == os.getenv(
            'LOG_FILE_PATH', LoggingConfig.DEFAULT_LOG_PATH
        )

    def test_configure_removes_existing_handlers_before_adding_new(self):
        LoggingConfig.configure(level=logging.DEBUG)
        first_handlers_count = len(LoggingConfig._handlers)

        LoggingConfig.reset()
        LoggingConfig.configure(level=logging.INFO)
        second_handlers_count = len(LoggingConfig._handlers)

        assert first_handlers_count == second_handlers_count

    def test_multiple_configure_calls_reconfigure(self):
        """Test that calling configure multiple times reconfigures the system."""
        LoggingConfig.configure(level=logging.WARNING)
        handlers_after_first = len(LoggingConfig._handlers)

        LoggingConfig.configure(level=logging.ERROR)
        handlers_after_second = len(LoggingConfig._handlers)

        # After code changes, configure can now be called multiple times
        # Handlers are reset and recreated, so count should remain consistent
        assert handlers_after_first == handlers_after_second
        # And the level should be the latest configured
        assert LoggingConfig._log_level == logging.ERROR
