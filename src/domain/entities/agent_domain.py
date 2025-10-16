from dataclasses import dataclass, field
from typing import Any, Dict

from src.domain.exceptions.domain_exceptions import (
    InvalidConfigTypeException,
    InvalidProviderException,
    UnsupportedConfigException,
)
from src.domain.value_objects import History, SupportedConfigs, SupportedProviders


@dataclass
class Agent:
    """
    Entidade de domínio que representa um agente de IA.

    Responsabilidades:
    - Manter a identidade e configuração do agente
    - Gerenciar o histórico de conversas através do Value Object History
    - Garantir a integridade dos dados do agente

    As validações de regras de negócio são executadas no __post_init__.
    A lógica de histórico é delegada ao Value Object History.
    """

    provider: str
    model: str
    name: str
    instructions: str
    history: History = field(default_factory=History)
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Inicializa o histórico se necessário e valida as configurações do agente.

        Raises:
            InvalidProviderException: Se o provider não for suportado
            UnsupportedConfigException: Se uma config não for suportada
            InvalidConfigTypeException: Se o tipo de uma config for inválido
            InvalidAgentConfigException: Se o valor de uma config for inválido
        """
        # Inicializa histórico se necessário
        if not isinstance(self.history, History):
            object.__setattr__(self, "history", History())

        # Valida provider
        if self.provider.lower() not in SupportedProviders.get_available_providers():
            raise InvalidProviderException(
                self.provider, SupportedProviders.get_available_providers()
            )

        # Valida configurações extras
        for key, value in self.config.items():
            # Verifica se a config é suportada
            if key not in SupportedConfigs.get_available_configs():
                raise UnsupportedConfigException(
                    key, SupportedConfigs.get_available_configs()
                )

            # Verifica se o tipo é permitido
            if not isinstance(value, (int, float, str, bool, list, dict, type(None))):
                raise InvalidConfigTypeException(key, type(value))

            # Valida o valor da config
            SupportedConfigs.validate_config(key, value)

    def add_user_message(self, content: str) -> None:
        """
        Adiciona uma mensagem do usuário ao histórico.

        Args:
            content: Conteúdo da mensagem
        """
        self.history.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """
        Adiciona uma mensagem do assistente ao histórico.

        Args:
            content: Conteúdo da mensagem
        """
        self.history.add_assistant_message(content)

    def clear_history(self) -> None:
        self.history.clear()
