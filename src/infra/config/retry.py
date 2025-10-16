"""
Utilitários para retry com backoff exponencial.

Fornece decorators e funções para adicionar retry automático
em operações que podem falhar temporariamente.
"""

import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from src.infra.config.logging_config import LoggingConfig


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator para retry com backoff exponencial e jitter.

    Args:
        max_attempts: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        backoff_factor: Fator de multiplicação do delay a cada tentativa
        exceptions: Tupla de exceções que devem causar retry
        jitter: Se True, adiciona variação aleatória ao delay (±10%)
                para prevenir thundering herd em sistemas distribuídos
        on_retry: Callback opcional chamado a cada retry (attempt, exception)

    Returns:
        Decorator function

    Example:
        >>> @retry_with_backoff(max_attempts=3, initial_delay=1.0, jitter=True)
        ... def api_call():
        ...     return requests.get("https://api.example.com")
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

                    # Chama callback customizado se fornecido
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(
                                f"Erro no callback de retry: {callback_error}"
                            )

                    # Aplica jitter se habilitado (variação de ±10%)
                    actual_delay = delay
                    if jitter:
                        jitter_factor = 1 + random.uniform(-0.1, 0.1)
                        actual_delay = delay * jitter_factor

                    logger.warning(
                        f"Tentativa {attempt}/{max_attempts} falhou: {str(e)}. "
                        f"Aguardando {actual_delay:.2f}s antes de retry..."
                    )

                    time.sleep(actual_delay)
                    delay *= backoff_factor

            # Nunca deve chegar aqui, mas por segurança
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
