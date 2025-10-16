from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CreateAgentInputDTO:
    """DTO para criação de um novo agente."""

    provider: str
    model: str
    name: str
    instructions: str
    config: Dict[str, Any] = field(default_factory=dict)
    history_max_size: int = 10

    def validate(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError(
                "O campo 'provider' é obrigatório, deve ser uma string e não pode estar vazio"
            )

        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError(
                "O campo 'model' é obrigatório, deve ser uma string e não pode estar vazio"
            )

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "O campo 'name' é obrigatório, deve ser uma string e não pode estar vazio"
            )

        if not isinstance(self.instructions, str) or not self.instructions.strip():
            raise ValueError(
                "O campo 'instructions' é obrigatório, deve ser uma string e não pode estar vazio"
            )

        if not isinstance(self.config, dict):
            raise ValueError("O campo 'config' deve ser um dicionário (dict)")

        if not isinstance(self.history_max_size, int) or self.history_max_size <= 0:
            raise ValueError("O campo 'history_max_size' deve ser um inteiro positivo")


@dataclass
class AgentConfigOutputDTO:
    """DTO para retornar configurações de um agente."""

    provider: str
    model: str
    name: str
    instructions: str
    config: Dict[str, Any]
    history: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "name": self.name,
            "instructions": self.instructions,
            "configs": self.config,
            "history": self.history,
        }


@dataclass
class ChatInputDTO:
    """DTO para entrada de mensagem de chat."""

    message: str

    def validate(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(
                "O campo 'message' é obrigatório, deve ser uma string e não pode estar vazio"
            )


@dataclass
class ChatOutputDTO:
    """DTO para resposta de chat."""

    response: str

    def to_dict(self) -> Dict:
        return {
            "response": self.response,
        }
