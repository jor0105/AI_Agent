"""
Configuração centralizada de logging para a aplicação.

Este módulo fornece um logger configurável que pode ser usado
em toda a aplicação para rastreamento e debugging.
"""

import logging
import sys
from typing import Optional


class LoggingConfig:
    """
    Configuração centralizada de logging.
    Fornece loggers configurados para diferentes módulos.
    """

    _configured: bool = False
    _log_level: int = logging.INFO

    @classmethod
    def configure(
        cls,
        level: int = logging.INFO,
        format_string: Optional[str] = None,
        include_timestamp: bool = True,
    ) -> None:
        """
        Configura o logging da aplicação.

        Args:
            level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_string: String de formato customizada (opcional)
            include_timestamp: Se deve incluir timestamp nos logs
        """
        if cls._configured:
            return

        cls._log_level = level

        # Define formato padrão
        if format_string is None:
            if include_timestamp:
                format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            else:
                format_string = "%(name)s - %(levelname)s - %(message)s"

        # Configura handler para stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)

        # Configura logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(handler)

        cls._configured = True

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
        """Reseta a configuração de logging (útil para testes)."""
        cls._configured = False
        logging.getLogger().handlers.clear()
