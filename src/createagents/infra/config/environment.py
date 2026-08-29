import os
import threading
from typing import ClassVar, Self

from dotenv import load_dotenv


class EnvironmentConfig:
    """A thread-safe singleton for managing environment configurations.

    It loads environment variables only once and uses a lock to ensure
    safety in multi-threaded environments.
    """

    _instance: ClassVar[Self | None] = None
    _initialized: ClassVar[bool] = False
    _cache: ClassVar[dict[str, str]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __new__(cls) -> Self:
        """Implement the singleton pattern with thread safety."""
        with cls._lock:
            instance = cls._instance

            if instance is None:
                instance = super().__new__(cls)
                cls._instance = instance

            return instance

    def __init__(self) -> None:
        """Initialize and load environment variables only once."""
        if not EnvironmentConfig._initialized:
            with EnvironmentConfig._lock:
                if not EnvironmentConfig._initialized:
                    load_dotenv()
                    EnvironmentConfig._initialized = True

    @classmethod
    def get_api_key(cls, key: str) -> str:
        """Retrieve an API key from environment variables.

        This method is thread-safe and reads directly from environment variables
        to prevent sensitive API keys from being held in memory cache.

        Args:
            key: The name of the environment variable.

        Returns:
            The value of the API key.

        Raises:
            OSError: If the variable is not found or is empty.

        """
        if not cls._initialized:
            cls()

        with cls._lock:
            api_key = os.getenv(key)

            if not api_key or not api_key.strip():
                raise OSError(
                    f"The environment variable '{key}' was not found or is empty. "
                    'Ensure it is defined in the .env file.'
                )

            return api_key.strip()

    @classmethod
    def get_env(cls, key: str, default: str | None = None) -> str | None:
        """Retrieve an environment variable with an optional default value.

        This method is thread-safe, cached, and validates for empty values.

        Args:
            key: The name of the environment variable.
            default: The default value to return if the variable does not exist.

        Returns:
            The value of the variable or the default.

        Note:
            Only real environment values are cached. Caching a default would
            pin the first caller's fallback for every later caller, and would
            hide a variable defined after the first read.

        """
        if not cls._initialized:
            cls()

        if key in cls._cache:
            return cls._cache[key]

        with cls._lock:
            if key in cls._cache:
                return cls._cache[key]

            value = os.getenv(key)

            if value is not None and value.strip():
                value = value.strip()
                cls._cache[key] = value
                return value

            return default

    @classmethod
    def get_int_env(cls, key: str, default: int) -> int:
        """Retrieve an environment variable as an integer.

        Args:
            key: The name of the environment variable.
            default: The value used when the variable is unset or unusable.

        Returns:
            The parsed integer, or `default` if the variable is missing or
            does not hold a valid integer.

        """
        raw = cls.get_env(key, str(default))
        if raw is None:
            return default

        try:
            return int(raw)
        except ValueError:
            return default

    @classmethod
    def reload(cls) -> None:
        """Reload environment variables from the .env file.

        This is useful for tests or runtime reconfigurations.
        This method is thread-safe.

        Example:
            >>> EnvironmentConfig.reload()

        """
        with cls._lock:
            load_dotenv(override=True)
            cls._cache.clear()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the variable cache. This method is thread-safe."""
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def reset(cls) -> None:
        """Completely resets the singleton. This method is thread-safe."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
            cls._cache.clear()
