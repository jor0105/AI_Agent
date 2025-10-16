import os
import threading
from typing import Dict, Optional

from dotenv import load_dotenv


class EnvironmentConfig:
    """
    Singleton thread-safe para gerenciar configurações de ambiente.
    Carrega as variáveis de ambiente apenas uma vez.
    Utiliza Lock para garantir segurança em ambientes multi-threaded.
    """

    _instance: Optional["EnvironmentConfig"] = None
    _initialized: bool = False
    _cache: Dict[str, str] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "EnvironmentConfig":
        """Implementa o padrão Singleton com thread-safety."""
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Inicializa e carrega variáveis de ambiente apenas uma vez."""
        if not EnvironmentConfig._initialized:
            with EnvironmentConfig._lock:
                # Double-checked locking
                if not EnvironmentConfig._initialized:
                    load_dotenv()
                    EnvironmentConfig._initialized = True

    @classmethod
    def get_api_key(cls, key: str) -> str:
        """
        Obtém uma chave de API das variáveis de ambiente.
        Usa cache para evitar múltiplas leituras do ambiente.
        Thread-safe.

        Args:
            key: Nome da variável de ambiente

        Returns:
            Valor da chave de API

        Raises:
            EnvironmentError: Se a variável não for encontrada ou estiver vazia
        """
        # Garante que o ambiente foi inicializado
        if not cls._initialized:
            cls()

        # Verifica se está em cache (leitura thread-safe)
        if key in cls._cache:
            return cls._cache[key]

        # Busca no ambiente com lock para escrita no cache
        with cls._lock:
            # Double-check após adquirir lock
            if key in cls._cache:
                return cls._cache[key]

            api_key = os.getenv(key)

            # Valida se a chave existe e não está vazia
            if not api_key or not api_key.strip():
                raise EnvironmentError(
                    f"A variável de ambiente '{key}' não foi encontrada ou está vazia. "
                    f"Certifique-se de que ela está definida no arquivo .env"
                )

            # Armazena em cache (já validado)
            api_key = api_key.strip()
            cls._cache[key] = api_key
            return api_key

    @classmethod
    def get_env(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Obtém uma variável de ambiente com valor padrão opcional.
        Thread-safe e com cache. Valida valores vazios.

        Args:
            key: Nome da variável de ambiente
            default: Valor padrão se a variável não existir

        Returns:
            Valor da variável ou default
        """
        # Garante que o ambiente foi inicializado
        if not cls._initialized:
            cls()

        # Verifica cache
        if key in cls._cache:
            return cls._cache[key]

        # Busca no ambiente com lock
        with cls._lock:
            if key in cls._cache:
                return cls._cache[key]

            value = os.getenv(key, default)

            # Cacheia apenas valores não vazios
            if value is not None and value.strip():
                value = value.strip()
                cls._cache[key] = value
                return value
            elif default is not None:
                return default

            return value

    @classmethod
    def reload(cls) -> None:
        """
        Recarrega variáveis de ambiente do arquivo .env.
        Útil para testes ou reconfigurações em runtime.
        Thread-safe.

        Example:
            >>> EnvironmentConfig.reload()  # Recarrega o .env
        """
        with cls._lock:
            load_dotenv(override=True)
            cls._cache.clear()

    @classmethod
    def clear_cache(cls) -> None:
        """Limpa o cache de variáveis. Thread-safe."""
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def reset(cls) -> None:
        """Reseta completamente o Singleton. Thread-safe."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
            cls._cache.clear()
