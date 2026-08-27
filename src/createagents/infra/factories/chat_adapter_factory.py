from ...application.interfaces import ChatRepository
from ..adapters import OllamaChatAdapter, OpenAIChatAdapter
from ..config import LoggingConfig


class ChatAdapterFactory:
    """Resolves a provider name to its concrete chat adapter.

    Every call returns a fresh adapter. Adapters own the metrics collected
    during their conversations, so sharing one between agents would make an
    agent report another agent's metrics.
    """

    __logger = LoggingConfig.get_logger(__name__)

    @classmethod
    def create(cls, provider: str) -> ChatRepository:
        """Create the adapter that implements `provider`.

        Args:
            provider: The provider name ("openai" or "ollama"),
                matched case-insensitively.

        Returns:
            A new adapter instance for the requested provider.

        Raises:
            ValueError: If the provider is not "openai" or "ollama".
        """
        provider_lower = provider.lower()

        cls.__logger.info('Creating chat adapter - Provider: %s', provider)

        if provider_lower == 'openai':
            return OpenAIChatAdapter()
        if provider_lower == 'ollama':
            return OllamaChatAdapter()

        cls.__logger.error('Invalid provider requested: %s', provider)
        raise ValueError(f'Invalid provider: {provider}.')
