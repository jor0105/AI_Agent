from typing import Dict, Tuple

from src.application.interfaces.chat_repository import ChatRepository
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter


class ChatAdapterFactory:
    """
    Factory para criar adapters de chat com cache.

    Lógica:
    - Se provider for "openai": usa OpenAI
    - etc...

    O cache evita a criação de múltiplas instâncias do mesmo adapter,
    melhorando performance e reduzindo overhead de inicialização.
    """

    __cache: Dict[Tuple[str, str], ChatRepository] = {}

    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
    ) -> ChatRepository:
        """
        Cria o adapter apropriado com cache.

        Args:
            model: Nome do modelo (ex: "gpt-4", "llama2")
            provider: Provider específico ("openai", "ollama")

        Returns:
            ChatRepository: Instância do adapter apropriado (cached se já existir)

        Raises:
            ValueError: Se provider não for "openai" ou "ollama"
        """
        # Normaliza o model para lowercase para garantir cache correto
        cache_key = (model.lower(), provider.lower())

        # Verifica se já existe no cache
        if cache_key in cls.__cache:
            return cls.__cache[cache_key]

        # Cria novo adapter baseado no provider
        provider_lower = provider.lower()
        match provider_lower:
            case "openai":
                adapter = OpenAIChatAdapter()
            case "ollama":
                adapter = OllamaChatAdapter()
            case _:
                raise ValueError(f"Provider inválido: {provider}.")

        # Armazena no cache
        cls.__cache[cache_key] = adapter

        return adapter

    @classmethod
    def clear_cache(cls) -> None:
        cls.__cache.clear()
