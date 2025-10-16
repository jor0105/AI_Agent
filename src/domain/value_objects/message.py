from dataclasses import dataclass
from enum import Enum
from typing import Dict


class MessageRole(str, Enum):
    """Enum para definir os papéis possíveis em uma mensagem."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Message:
    """
    Value Object que representa uma mensagem no chat.
    Imutável para garantir integridade dos dados.
    """

    role: MessageRole
    content: str

    def __post_init__(self) -> None:
        """Valida os dados da mensagem."""
        if not isinstance(self.role, MessageRole):
            raise ValueError("Role deve ser uma instância de MessageRole")

        if not self.content or not self.content.strip():
            raise ValueError("O conteúdo da mensagem não pode estar vazio")

    def to_dict(self) -> Dict[str, str]:
        """
        Converte a mensagem para um dicionário.

        Returns:
            Dict com role e content
        """
        return {"role": self.role.value, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Message":
        """
        Cria uma instância de Message a partir de um dicionário.

        Args:
            data: Dicionário com 'role' e 'content'

        Returns:
            Nova instância de Message

        Raises:
            ValueError: Se o dicionário não contiver os campos necessários
        """
        if "role" not in data or "content" not in data:
            raise ValueError("Dicionário deve conter 'role' e 'content'")

        try:
            role = MessageRole(data["role"])
        except ValueError:
            raise ValueError(
                f"Role inválido: '{data['role']}'. Valores válidos: {[r.value for r in MessageRole]}"
            )

        return cls(role=role, content=data["content"])
