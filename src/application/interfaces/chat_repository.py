from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ChatRepository(ABC):
    @abstractmethod
    def chat(
        self,
        model: str,
        instructions: str,
        config: Dict[str, Any],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        pass
