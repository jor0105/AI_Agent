from abc import ABC, abstractmethod
from typing import Dict, List


class ChatRepository(ABC):
    @abstractmethod
    def chat(
        self,
        model: str,
        instructions: str,
        user_input: List[Dict[str, str]],
    ) -> str:
        pass
