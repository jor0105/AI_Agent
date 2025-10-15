from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class ChatRepository(ABC):
    @abstractmethod
    def chat(
        self,
        model: str,
        instructions: str,
        user_ask: str,
        history: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        pass
