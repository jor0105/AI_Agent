from typing import Set


class SupportedProviders:
    """
    Classe para gerenciar providers disponíveis.
    """

    __AVAILABLE_PROVIDERS: Set[str] = {"openai", "ollama"}

    @classmethod
    def get_available_providers(cls) -> Set[str]:
        """
        Retorna o conjunto de providers disponíveis.

        Returns:
            Set[str]: Conjunto com nomes dos providers disponíveis
        """
        return cls.__AVAILABLE_PROVIDERS
