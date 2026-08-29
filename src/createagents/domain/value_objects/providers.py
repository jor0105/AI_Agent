from typing import ClassVar


class SupportedProviders:
    """Manages the available AI providers.

    Responsibilities:
    - Define the providers supported by the system.
    - Provide an interface for querying available providers.
    """

    __AVAILABLE_PROVIDERS: ClassVar[set[str]] = {'openai', 'ollama'}

    @classmethod
    def get_available_providers(cls) -> set[str]:
        """Return a set of the available providers.

        Returns:
            A set containing the names of the available providers.

        """
        return cls.__AVAILABLE_PROVIDERS.copy()
