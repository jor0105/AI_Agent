"""
Utilitários para retry com backoff exponencial.

Fornece decorators e funções para adicionar retry automático
em operações que podem falhar temporariamente.
"""

import time
from functools import wraps
from typing import Callable, Tuple, Type

from src.infra.config.logging_config import LoggingConfig


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator para retry com backoff exponencial.

    Args:
        max_attempts: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        backoff_factor: Fator de multiplicação do delay a cada tentativa
        exceptions: Tupla de exceções que devem causar retry

    Returns:
        Decorator function
    """
    logger = LoggingConfig.get_logger(__name__)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(f"Falha após {max_attempts} tentativas: {str(e)}")
                        raise

                    logger.warning(
                        f"Tentativa {attempt}/{max_attempts} falhou: {str(e)}. "
                        f"Aguardando {delay:.2f}s antes de retry..."
                    )

                    time.sleep(delay)
                    delay *= backoff_factor

            # Nunca deve chegar aqui, mas por segurança
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
