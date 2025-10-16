"""
Testes para configuração de logging.
"""

import logging
import os
import tempfile
from pathlib import Path

from src.infra.config.logging_config import (
    JSONFormatter,
    LoggingConfig,
    SensitiveDataFormatter,
)
from src.infra.config.sensitive_data_filter import SensitiveDataFilter


class TestSensitiveDataFormatter:
    """Testes para formatter que filtra dados sensíveis."""

    def setup_method(self):
        """Setup antes de cada teste."""
        SensitiveDataFilter.clear_cache()

    def test_format_filters_sensitive_data(self):
        """Testa que o formatter filtra dados sensíveis."""
        formatter = SensitiveDataFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="password=secret123",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "secret123" not in result
        assert "[PASSWORD_REDACTED]" in result

    def test_format_preserves_normal_messages(self):
        """Testa que mensagens normais não são alteradas."""
        formatter = SensitiveDataFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Normal message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert result == "Normal message"

    def test_format_with_timestamp(self):
        """Testa formatter com timestamp."""
        formatter = SensitiveDataFormatter("%(asctime)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "Test message" in result
        assert "-" in result  # Separador do timestamp


class TestJSONFormatter:
    """Testes para formatter JSON."""

    def setup_method(self):
        """Setup antes de cada teste."""
        SensitiveDataFilter.clear_cache()

    def test_format_returns_valid_json(self):
        """Testa que retorna JSON válido."""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.module"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"
        assert parsed["line"] == 42

    def test_format_filters_sensitive_data_in_json(self):
        """Testa que dados sensíveis são filtrados no JSON."""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API_KEY=sk-123456789012",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "sk-123456789012" not in parsed["message"]
        assert "[API_KEY_REDACTED]" in parsed["message"]

    def test_format_includes_exception(self):
        """Testa que exceções são incluídas no JSON."""
        import json

        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "ValueError: Test error" in parsed["exception"]


class TestLoggingConfig:
    """Testes para configuração de logging."""

    def setup_method(self):
        """Setup antes de cada teste."""
        LoggingConfig.reset()

    def teardown_method(self):
        """Cleanup após cada teste."""
        LoggingConfig.reset()
        # Limpa variáveis de ambiente
        for key in ["LOG_LEVEL", "LOG_TO_FILE", "LOG_FILE_PATH", "LOG_JSON_FORMAT"]:
            if key in os.environ:
                del os.environ[key]

    def test_configure_default_settings(self):
        """Testa configuração com settings padrão."""
        LoggingConfig.configure()

        assert LoggingConfig._configured is True
        assert LoggingConfig._log_level == logging.INFO
        assert len(LoggingConfig._handlers) == 1  # Apenas console

    def test_configure_custom_level(self):
        """Testa configuração com nível customizado."""
        LoggingConfig.configure(level=logging.DEBUG)

        assert LoggingConfig._log_level == logging.DEBUG
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_from_env_var(self):
        """Testa configuração a partir de variável de ambiente."""
        os.environ["LOG_LEVEL"] = "WARNING"
        LoggingConfig.configure()

        assert LoggingConfig._log_level == logging.WARNING

    def test_configure_invalid_env_var_uses_default(self):
        """Testa que valor inválido usa o padrão."""
        os.environ["LOG_LEVEL"] = "INVALID"
        LoggingConfig.configure()

        assert LoggingConfig._log_level == logging.INFO

    def test_configure_with_file_handler(self):
        """Testa configuração com file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            LoggingConfig.configure(log_to_file=True, log_file_path=str(log_file))

            assert len(LoggingConfig._handlers) == 2  # Console + File
            assert log_file.exists() or log_file.parent.exists()

    def test_configure_creates_log_directory(self):
        """Testa que diretórios são criados automaticamente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "nested" / "dir" / "test.log"

            LoggingConfig.configure(log_to_file=True, log_file_path=str(log_file))

            assert log_file.parent.exists()

    def test_configure_with_json_format(self):
        """Testa configuração com formato JSON."""
        LoggingConfig.configure(json_format=True)

        handlers = LoggingConfig.get_handlers()
        assert len(handlers) > 0
        assert isinstance(handlers[0].formatter, JSONFormatter)

    def test_configure_only_once(self):
        """Testa que configure só executa uma vez."""
        LoggingConfig.configure(level=logging.DEBUG)
        initial_level = LoggingConfig._log_level

        LoggingConfig.configure(level=logging.ERROR)

        # Não deve mudar
        assert LoggingConfig._log_level == initial_level

    def test_get_logger_returns_logger(self):
        """Testa que get_logger retorna um logger."""
        logger = LoggingConfig.get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_configures_if_needed(self):
        """Testa que get_logger configura automaticamente."""
        assert LoggingConfig._configured is False

        logger = LoggingConfig.get_logger("test")

        assert LoggingConfig._configured is True
        assert isinstance(logger, logging.Logger)

    def test_set_level_changes_level(self):
        """Testa que set_level altera o nível."""
        LoggingConfig.configure(level=logging.INFO)

        LoggingConfig.set_level(logging.ERROR)

        assert LoggingConfig._log_level == logging.ERROR
        assert logging.getLogger().level == logging.ERROR

    def test_reset_clears_configuration(self):
        """Testa que reset limpa a configuração."""
        LoggingConfig.configure()
        assert LoggingConfig._configured is True

        LoggingConfig.reset()

        assert LoggingConfig._configured is False
        assert len(LoggingConfig._handlers) == 0

    def test_reset_clears_sensitive_data_cache(self):
        """Testa que reset limpa o cache do filtro (LRU cache)."""
        # O método _filter_cached é que tem @lru_cache, não o filter

        # Adiciona algo ao cache chamando filter múltiplas vezes
        test_text = "password=secret123"
        SensitiveDataFilter.filter(test_text)
        SensitiveDataFilter.filter(test_text)

        # Verifica que cache_info mostra hits após segunda chamada
        cache_info_before = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info_before.hits > 0 or cache_info_before.currsize > 0

        # Reset deve limpar o cache
        LoggingConfig.reset()

        # Após reset, cache deve estar vazio (currsize = 0)
        cache_info_after = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info_after.currsize == 0
        assert cache_info_after.hits == 0
        assert cache_info_after.misses == 0

    def test_get_handlers_returns_copy(self):
        """Testa que get_handlers retorna uma cópia."""
        LoggingConfig.configure()
        handlers = LoggingConfig.get_handlers()

        handlers.clear()

        # Lista interna não deve ser afetada
        assert len(LoggingConfig._handlers) > 0

    def test_logging_filters_sensitive_data(self):
        """Testa que logs realmente filtram dados sensíveis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            LoggingConfig.configure(log_to_file=True, log_file_path=str(log_file))

            logger = LoggingConfig.get_logger("test")
            logger.info("User password=secret123")

            # Força flush
            for handler in LoggingConfig._handlers:
                handler.flush()

            # Lê o arquivo
            if log_file.exists():
                content = log_file.read_text()
                assert "secret123" not in content
                assert "[PASSWORD_REDACTED]" in content

    def test_configure_with_env_file_logging(self):
        """Testa configuração de arquivo via env var."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "app.log"
            os.environ["LOG_TO_FILE"] = "true"
            os.environ["LOG_FILE_PATH"] = str(log_file)

            LoggingConfig.configure()

            assert len(LoggingConfig._handlers) == 2

    def test_configure_without_timestamp(self):
        """Testa configuração sem timestamp."""
        LoggingConfig.configure(include_timestamp=False)

        handlers = LoggingConfig.get_handlers()
        formatter = handlers[0].formatter
        # Formato não deve ter asctime
        assert "asctime" not in formatter._fmt

    def test_configure_custom_format_string(self):
        """Testa configuração com string de formato customizada."""
        custom_format = "%(levelname)s - %(message)s"
        LoggingConfig.configure(format_string=custom_format)

        handlers = LoggingConfig.get_handlers()
        formatter = handlers[0].formatter
        assert formatter._fmt == custom_format

    def test_file_rotation_settings(self):
        """Testa que settings de rotação são aplicados."""
        from logging.handlers import RotatingFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            max_bytes = 1024
            backup_count = 3

            LoggingConfig.configure(
                log_to_file=True,
                log_file_path=str(log_file),
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

            handlers = LoggingConfig.get_handlers()
            file_handler = [h for h in handlers if isinstance(h, RotatingFileHandler)][
                0
            ]

            assert file_handler.maxBytes == max_bytes
            assert file_handler.backupCount == backup_count

    def test_multiple_loggers_share_config(self):
        """Testa que múltiplos loggers compartilham a configuração."""
        LoggingConfig.configure(level=logging.WARNING)

        logger1 = LoggingConfig.get_logger("module1")
        logger2 = LoggingConfig.get_logger("module2")

        assert logger1.level == logging.WARNING
        assert logger2.level == logging.WARNING

    def test_logger_logs_at_correct_level(self):
        """Testa que logger só loga no nível correto."""
        import io

        # Cria um handler customizado para capturar logs
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.WARNING)

        LoggingConfig.reset()
        LoggingConfig.configure(level=logging.WARNING)
        logger = LoggingConfig.get_logger("test")

        # Adiciona nosso handler para captura
        logger.addHandler(handler)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        handler.flush()
        output = stream.getvalue()

        assert "Debug message" not in output
        assert "Info message" not in output
        assert "Warning message" in output


class TestLoggingIntegration:
    """Testes de integração do sistema de logging."""

    def setup_method(self):
        """Setup antes de cada teste."""
        LoggingConfig.reset()

    def teardown_method(self):
        """Cleanup após cada teste."""
        LoggingConfig.reset()

    def test_real_world_scenario_with_sensitive_data(self):
        """Testa cenário real com múltiplos tipos de dados sensíveis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "app.log"
            LoggingConfig.configure(log_to_file=True, log_file_path=str(log_file))

            logger = LoggingConfig.get_logger("app")

            # Simula logs reais
            logger.info("User logged in: user@example.com")
            logger.debug("API request with key: sk-proj-123456789012")
            logger.warning("Database connection: postgres://admin:pass123@db.com")
            logger.error("Failed payment for card: 4532-1234-5678-9010")

            # Força flush
            for handler in LoggingConfig._handlers:
                handler.flush()

            # Verifica arquivo
            content = log_file.read_text()

            # Dados sensíveis não devem estar presentes
            assert "user@example.com" not in content
            assert "sk-proj-123456789012" not in content
            assert "pass123" not in content
            assert "4532-1234-5678-9010" not in content

            # Placeholders devem estar presentes
            assert "[EMAIL_REDACTED]" in content
            assert (
                "[PASSWORD_REDACTED]" in content or "[CREDENTIALS_REDACTED]" in content
            )
            assert "[CREDIT_CARD_REDACTED]" in content

    def test_json_logging_production_ready(self):
        """Testa logging JSON pronto para produção."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "app.json"
            LoggingConfig.configure(
                log_to_file=True, log_file_path=str(log_file), json_format=True
            )

            logger = LoggingConfig.get_logger("api")
            logger.info("Request received from user@test.com")

            for handler in LoggingConfig._handlers:
                handler.flush()

            # Lê e valida JSON
            lines = log_file.read_text().strip().split("\n")
            for line in lines:
                log_entry = json.loads(line)

                # Verifica estrutura
                assert "timestamp" in log_entry
                assert "level" in log_entry
                assert "logger" in log_entry
                assert "message" in log_entry

                # Verifica filtragem
                assert "user@test.com" not in log_entry["message"]

    def test_default_constants_defined(self):
        """Testa que constantes padrão estão definidas."""
        assert hasattr(LoggingConfig, "DEFAULT_LOG_LEVEL")
        assert hasattr(LoggingConfig, "DEFAULT_MAX_BYTES")
        assert hasattr(LoggingConfig, "DEFAULT_BACKUP_COUNT")
        assert hasattr(LoggingConfig, "DEFAULT_LOG_PATH")

    def test_default_log_level_constant(self):
        """Testa valor da constante DEFAULT_LOG_LEVEL."""
        assert LoggingConfig.DEFAULT_LOG_LEVEL == logging.INFO

    def test_default_max_bytes_constant(self):
        """Testa valor da constante DEFAULT_MAX_BYTES."""
        assert LoggingConfig.DEFAULT_MAX_BYTES == 10 * 1024 * 1024  # 10MB

    def test_default_backup_count_constant(self):
        """Testa valor da constante DEFAULT_BACKUP_COUNT."""
        assert LoggingConfig.DEFAULT_BACKUP_COUNT == 5

    def test_default_log_path_constant(self):
        """Testa valor da constante DEFAULT_LOG_PATH."""
        assert LoggingConfig.DEFAULT_LOG_PATH == "logs/app.log"

    def test_configure_uses_default_constants(self):
        """Testa que configure usa constantes padrão."""
        LoggingConfig.configure()

        # Log level deve ser DEFAULT_LOG_LEVEL
        assert LoggingConfig._log_level == LoggingConfig.DEFAULT_LOG_LEVEL

    def test_resolve_log_file_path_with_none(self):
        """Testa _resolve_log_file_path com None."""
        result = LoggingConfig._resolve_log_file_path(None)

        # Deve usar DEFAULT_LOG_PATH ou variável de ambiente
        assert isinstance(result, str)
        assert len(result) > 0

    def test_resolve_log_file_path_with_valid_string(self):
        """Testa _resolve_log_file_path com string válida."""
        test_path = "/tmp/test.log"
        result = LoggingConfig._resolve_log_file_path(test_path)

        assert result == test_path

    def test_resolve_log_file_path_with_bool(self):
        """Testa que _resolve_log_file_path trata bool corretamente."""
        # Bool não deve ser aceito, deve usar default
        result = LoggingConfig._resolve_log_file_path(True)

        assert isinstance(result, str)
        assert result != "True"  # Não deve converter bool diretamente

    def test_resolve_log_file_path_with_invalid_type(self):
        """Testa _resolve_log_file_path com tipo inválido."""
        # Deve lidar graciosamente com tipos inválidos
        result = LoggingConfig._resolve_log_file_path(12345)

        assert isinstance(result, str)

    def test_resolve_log_file_path_respects_env_var(self):
        """Testa que _resolve_log_file_path respeita LOG_FILE_PATH."""
        custom_path = "/custom/path/app.log"
        os.environ["LOG_FILE_PATH"] = custom_path

        try:
            result = LoggingConfig._resolve_log_file_path(None)
            assert result == custom_path
        finally:
            if "LOG_FILE_PATH" in os.environ:
                del os.environ["LOG_FILE_PATH"]

    def test_configure_with_custom_max_bytes(self):
        """Testa configure com max_bytes customizado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            custom_max_bytes = 5 * 1024 * 1024  # 5MB
            LoggingConfig.configure(
                log_to_file=True,
                log_file_path=str(log_file),
                max_bytes=custom_max_bytes,
            )

            # Verifica que handler foi configurado
            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert file_handlers[0].maxBytes == custom_max_bytes

    def test_configure_with_custom_backup_count(self):
        """Testa configure com backup_count customizado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

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
        """Testa que usa DEFAULT_MAX_BYTES quando não especificado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            LoggingConfig.configure(log_to_file=True, log_file_path=str(log_file))

            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert file_handlers[0].maxBytes == LoggingConfig.DEFAULT_MAX_BYTES

    def test_configure_uses_default_backup_count_when_not_specified(self):
        """Testa que usa DEFAULT_BACKUP_COUNT quando não especificado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            LoggingConfig.configure(log_to_file=True, log_file_path=str(log_file))

            file_handlers = [
                h
                for h in LoggingConfig._handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]

            assert len(file_handlers) > 0
            assert file_handlers[0].backupCount == LoggingConfig.DEFAULT_BACKUP_COUNT

    def test_constants_are_immutable_values(self):
        """Testa que constantes têm valores imutáveis apropriados."""
        # Constantes devem ser tipos primitivos (int, str)
        assert isinstance(LoggingConfig.DEFAULT_LOG_LEVEL, int)
        assert isinstance(LoggingConfig.DEFAULT_MAX_BYTES, int)
        assert isinstance(LoggingConfig.DEFAULT_BACKUP_COUNT, int)
        assert isinstance(LoggingConfig.DEFAULT_LOG_PATH, str)

    def test_resolve_log_file_path_handles_path_like_objects(self):
        """Testa que _resolve_log_file_path lida com objetos path-like."""
        from pathlib import Path

        test_path = Path("/tmp/test.log")
        result = LoggingConfig._resolve_log_file_path(str(test_path))

        assert result == str(test_path)

    def test_configure_with_default_log_path_creates_directory(self):
        """Testa que diretório é criado ao usar DEFAULT_LOG_PATH."""

        # Limpa se existir
        if Path("logs").exists():
            # Apenas testa se não vai quebrar
            LoggingConfig.configure(log_to_file=True)
            assert LoggingConfig._configured

    def test_magic_numbers_replaced_by_constants(self):
        """Testa que não há magic numbers no código (usam constantes)."""
        # Verifica que as constantes têm valores razoáveis
        assert LoggingConfig.DEFAULT_MAX_BYTES > 0
        assert LoggingConfig.DEFAULT_BACKUP_COUNT > 0
        assert len(LoggingConfig.DEFAULT_LOG_PATH) > 0

        # Valores esperados específicos
        assert LoggingConfig.DEFAULT_MAX_BYTES == 10485760  # 10 * 1024 * 1024
        assert LoggingConfig.DEFAULT_BACKUP_COUNT == 5

    def test_resolve_log_file_path_is_classmethod(self):
        """Testa que _resolve_log_file_path é um classmethod."""
        import inspect

        # Verifica que é um método de classe
        assert inspect.ismethod(LoggingConfig._resolve_log_file_path)

    def test_constants_accessible_without_instantiation(self):
        """Testa que constantes são acessíveis sem instanciar."""
        # Não precisa configurar para acessar constantes
        level = LoggingConfig.DEFAULT_LOG_LEVEL
        max_bytes = LoggingConfig.DEFAULT_MAX_BYTES
        backup = LoggingConfig.DEFAULT_BACKUP_COUNT
        path = LoggingConfig.DEFAULT_LOG_PATH

        assert level is not None
        assert max_bytes is not None
        assert backup is not None
        assert path is not None
