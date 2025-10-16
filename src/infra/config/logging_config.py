"""
Configuração centralizada de logging para a aplicação.

Este módulo fornece um logger configurável que pode ser usado
em toda a aplicação para rastreamento e debugging.

Features:
- Filtragem automática de dados sensíveis
- Rotação de arquivos de log
- Configuração por variáveis de ambiente
- Logs estruturados (JSON) opcional
- Diferentes handlers para console e arquivo
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional

from src.infra.config.sensitive_data_filter import SensitiveDataFilter


class SensitiveDataFormatter(logging.Formatter):
    """
    Formatter que aplica filtro de dados sensíveis.
    Garante que nenhum dado sensível seja logado.
    """

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return SensitiveDataFilter.filter(original)


class JSONFormatter(logging.Formatter):
    """
    Formatter para logs estruturados em JSON.
    Útil para integração com ferramentas de análise de logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Aplica filtro de dados sensíveis no JSON
        json_str = json.dumps(log_data, ensure_ascii=False)
        return SensitiveDataFilter.filter(json_str)


class LoggingConfig:
    """
    Configuração centralizada de logging.
    Fornece loggers configurados para diferentes módulos com:
    - Filtragem de dados sensíveis
    - Rotação de arquivos
    - Configuração por ambiente
    """

    # Constantes de configuração
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_LOG_PATH = "logs/app.log"

    _configured: bool = False
    _log_level: int = DEFAULT_LOG_LEVEL
    # Tipagem explícita para evitar avisos de tipo
    _handlers: List[logging.Handler] = []

    @classmethod
    def configure(
        cls,
        level: Optional[int] = None,
        format_string: Optional[str] = None,
        include_timestamp: bool = True,
        log_to_file: bool = False,
        log_file_path: Optional[str] = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        json_format: bool = False,
    ) -> None:
        """
        Configura o logging da aplicação.

        Args:
            level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Se None, lê de LOG_LEVEL env var (default: INFO)
            format_string: String de formato customizada (opcional)
            include_timestamp: Se deve incluir timestamp nos logs
            log_to_file: Se deve logar em arquivo além do console
            log_file_path: Caminho do arquivo de log. Se None, usa LOG_FILE_PATH env var
            max_bytes: Tamanho máximo do arquivo antes de rotacionar (default: 10MB)
            backup_count: Número de arquivos de backup a manter (default: 5)
            json_format: Se deve usar formato JSON estruturado
        """
        if cls._configured:
            return

        # Lê configurações do ambiente
        level = level or cls._get_log_level_from_env()
        log_to_file = log_to_file or os.getenv("LOG_TO_FILE", "false").lower() == "true"

        # Resolve caminho do arquivo de log
        log_file_path = cls._resolve_log_file_path(log_file_path)

        json_format = (
            json_format or os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
        )

        cls._log_level = level

        # Define formato padrão
        if format_string is None:
            if include_timestamp:
                format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            else:
                format_string = "%(name)s - %(levelname)s - %(message)s"

        # Configura logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        cls._handlers.clear()

        # Configura formatter com filtro de dados sensíveis
        if json_format:
            formatter: logging.Formatter = JSONFormatter()
        else:
            # logging.Formatter aceita um fmt opcional
            formatter = SensitiveDataFormatter(format_string)

        # Handler para console (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        cls._handlers.append(console_handler)

        # Handler para arquivo com rotação (se habilitado)
        if log_to_file:
            # Cria diretório se não existir
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # RotatingFileHandler espera um caminho de arquivo (str ou file descriptor).
            file_handler = RotatingFileHandler(
                str(log_file_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            cls._handlers.append(file_handler)

        cls._configured = True

    @classmethod
    def _resolve_log_file_path(cls, log_file_path: Optional[str]) -> str:
        """
        Resolve e valida o caminho do arquivo de log.
        Extrai a lógica complexa de validação para melhor legibilidade.

        Args:
            log_file_path: Caminho fornecido ou None

        Returns:
            Caminho válido como string
        """
        default_path = os.getenv("LOG_FILE_PATH", cls.DEFAULT_LOG_PATH)

        # Se None ou bool inválido, usa default
        if log_file_path is None or isinstance(log_file_path, bool):
            return default_path

        # Tenta converter para string
        try:
            return str(log_file_path)
        except Exception:
            return default_path

    @classmethod
    def _get_log_level_from_env(cls) -> int:
        """
        Obtém o nível de log da variável de ambiente LOG_LEVEL.

        Returns:
            Nível de logging (default: INFO)
        """
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_name, logging.INFO)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtém um logger configurado para o módulo especificado.

        Args:
            name: Nome do módulo (geralmente __name__)

        Returns:
            Logger configurado
        """
        if not cls._configured:
            cls.configure()

        logger = logging.getLogger(name)
        logger.setLevel(cls._log_level)
        return logger

    @classmethod
    def set_level(cls, level: int) -> None:
        """
        Ajusta o nível de logging em runtime.

        Args:
            level: Novo nível de logging
        """
        cls._log_level = level
        logging.getLogger().setLevel(level)

    @classmethod
    def reset(cls) -> None:
        """
        Reseta a configuração de logging (útil para testes).
        Remove todos os handlers e marca como não configurado.
        """
        cls._configured = False
        root_logger = logging.getLogger()

        for handler in cls._handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        cls._handlers.clear()
        SensitiveDataFilter.clear_cache()

    @classmethod
    def get_handlers(cls) -> list:
        """
        Retorna a lista de handlers configurados.

        Returns:
            Lista de handlers ativos
        """
        return cls._handlers.copy()
