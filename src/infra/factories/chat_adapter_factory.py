from typing import Dict, Literal, Tuple

from src.application.interfaces.chat_repository import ChatRepository
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter

ProviderType = Literal["openai", "ollama"]


class ChatAdapterFactory:
    """
    Factory para criar adapters de chat com cache.

    Lógica:
    - Se provider for "openai": usa OpenAI
    - Se provider for "ollama": usa Ollama

    O cache evita a criação de múltiplas instâncias do mesmo adapter,
    melhorando performance e reduzindo overhead de inicialização.
    """

    _cache: Dict[Tuple[str, str], ChatRepository] = {}

    @classmethod
    def create(
        cls,
        provider: ProviderType,
        model: str,
    ) -> ChatRepository:
        """
        Cria o adapter apropriado com cache.

        Args:
            model: Nome do modelo (ex: "gpt-4", "llama2")
            provider: Provider específico ("openai" ou "ollama")

        Returns:
            ChatRepository: Instância do adapter apropriado (cached se já existir)

        Raises:
            ValueError: Se provider não for "openai" ou "ollama"
        """
        # Normaliza o model para lowercase para garantir cache correto
        cache_key = (model.lower(), provider)

        # Verifica se já existe no cache
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Cria novo adapter baseado no provider
        if provider == "openai":
            adapter = OpenAIChatAdapter()
        elif provider == "ollama":
            adapter = OllamaChatAdapter()
        else:
            raise ValueError(
                f"Provider inválido: {provider}. Use 'openai' ou 'ollama'."
            )

        # Armazena no cache
        cls._cache[cache_key] = adapter

        return adapter

    @classmethod
    def clear_cache(cls) -> None:
        """
        Limpa o cache de adapters.
        Útil para testes ou quando se deseja forçar recriação.
        """
        cls._cache.clear()
