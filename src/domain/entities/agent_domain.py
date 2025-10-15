from dataclasses import dataclass, field

from src.domain.value_objects import History


@dataclass
class Agent:
    """
    Entidade de domínio que representa um agente de IA.

    Responsabilidades:
    - Manter a identidade e configuração do agente
    - Gerenciar o histórico de conversas através do Value Object History

    As validações são delegadas aos DTOs (fail-fast na entrada).
    A lógica de histórico é delegada ao Value Object History.
    """

    provider: str
    model: str
    name: str
    instructions: str
    history: History = field(default_factory=History)

    def __post_init__(self):
        """Inicializa o histórico se necessário."""
        # Se history_max_size foi passado como int em vez de History, cria History
        if not isinstance(self.history, History):
            object.__setattr__(self, "history", History())

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
