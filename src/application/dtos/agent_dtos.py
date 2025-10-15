from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CreateAgentInputDTO:
    """DTO para criação de um novo agente."""

    provider: str
    model: str
    name: str
    instructions: str
    history_max_size: int = 10

    def validate(self) -> None:
        if not self.model or not self.model.strip():
            raise ValueError("O campo 'model' é obrigatório e não pode estar vazio")

        if not self.name or not self.name.strip():
            raise ValueError("O campo 'name' é obrigatório e não pode estar vazio")

        if not self.instructions or not self.instructions.strip():
            raise ValueError(
                "O campo 'instructions' é obrigatório e não pode estar vazio"
            )

        if self.history_max_size <= 0:
            raise ValueError("O campo 'history_max_size' deve ser maior que zero")

        if self.provider not in ("openai", "ollama"):
            raise ValueError("O campo 'provider' deve ser 'openai' ou 'ollama'")


@dataclass
class AgentConfigOutputDTO:
    """DTO para retornar configurações de um agente."""

    provider: str
    model: str
    name: str
    instructions: str
    history: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "name": self.name,
            "instructions": self.instructions,
            "history": self.history,
        }


@dataclass
class ChatInputDTO:
    """DTO para entrada de mensagem de chat."""

    message: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[List[str]] = None

    def validate(self) -> None:
        if not self.message or not self.message.strip():
            raise ValueError("A mensagem não pode estar vazia")

        if self.temperature is not None and not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature deve estar entre 0.0 e 2.0")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens deve ser maior que zero")

        if self.top_p is not None and not (0.0 <= self.top_p <= 1.0):
            raise ValueError("top_p deve estar entre 0.0 e 1.0")


@dataclass
class ChatOutputDTO:
    """DTO para resposta de chat."""

    response: str

    def to_dict(self) -> Dict:
        return {
            "response": self.response,
        }
