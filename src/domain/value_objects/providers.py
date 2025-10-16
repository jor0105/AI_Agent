from typing import Set


class SupportedProviders:
    """
    Value Object responsável por gerenciar providers de IA disponíveis.

    Responsabilidades:
    - Definir providers suportados pelo sistema
    - Prover interface para consulta de providers disponíveis
    """

    __AVAILABLE_PROVIDERS: Set[str] = {"openai", "ollama"}

    @classmethod
    def get_available_providers(cls) -> Set[str]:
        """
        Retorna o conjunto de providers disponíveis.

        Returns:
            Set[str]: Conjunto com nomes dos providers disponíveis (cópia)
        """
        return cls.__AVAILABLE_PROVIDERS.copy()
