from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List

from .message import Message, MessageRole


@dataclass
class History:
    """
    Value Object que gerencia o histórico de mensagens do chat.
    Encapsula a lógica de limite de tamanho do histórico.

    Utiliza deque com maxlen para performance otimizada,
    removendo automaticamente mensagens antigas sem recriar estrutura.
    """

    max_size: int = 10
    _messages: Deque[Message] = field(default_factory=deque)

    def __post_init__(self) -> None:
        if not isinstance(self.max_size, int) or self.max_size <= 0:
            raise ValueError("Tamanho máximo do histórico deve ser maior que zero")

        # Converte _messages para deque com maxlen, independente do tipo inicial
        messages = list(self._messages) if self._messages else []
        object.__setattr__(self, "_messages", deque(messages, maxlen=self.max_size))

    def add(self, message: Message) -> None:
        """
        Adiciona uma mensagem ao histórico.
        O deque com maxlen mantém automaticamente o limite de tamanho.

        Args:
            message: Mensagem a ser adicionada
        """
        if not isinstance(message, Message):
            raise TypeError("Apenas objetos do tipo Message podem ser adicionados")

        self._messages.append(message)

    def add_user_message(self, content: str) -> None:
        """
        Atalho para adicionar uma mensagem do usuário.

        Args:
            content: Conteúdo da mensagem
        """
        message = Message(role=MessageRole.USER, content=content)
        self.add(message)

    def add_assistant_message(self, content: str) -> None:
        """
        Atalho para adicionar uma mensagem do assistente.

        Args:
            content: Conteúdo da mensagem
        """
        message = Message(role=MessageRole.ASSISTANT, content=content)
        self.add(message)

    def add_system_message(self, content: str) -> None:
        """
        Atalho para adicionar uma mensagem do sistema.

        Args:
            content: Conteúdo da mensagem
        """
        message = Message(role=MessageRole.SYSTEM, content=content)
        self.add(message)

    def clear(self) -> None:
        """Limpa todo o histórico de mensagens."""
        self._messages.clear()

    def get_messages(self) -> List[Message]:
        """
        Retorna uma cópia da lista de mensagens.

        Returns:
            Lista de mensagens
        """
        return list(self._messages)

    def to_dict_list(self) -> List[Dict[str, str]]:
        """
        Converte o histórico para uma lista de dicionários.

        Returns:
            Lista de dicionários com role e content
        """
        return [message.to_dict() for message in self._messages]

    @classmethod
    def from_dict_list(cls, data: List[Dict[str, str]], max_size: int) -> "History":
        """
        Cria uma instância de History a partir de uma lista de dicionários.

        Args:
            data: Lista de dicionários com 'role' e 'content'
            max_size: Tamanho máximo do histórico

        Returns:
            Nova instância de History
        """
        history = cls(max_size=max_size)
        for item in data:
            message = Message.from_dict(item)
            history.add(message)
        return history

    def __len__(self) -> int:
        return len(self._messages)

    def __bool__(self) -> bool:
        return bool(self._messages)
