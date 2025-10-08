from abc import ABC, abstractmethod
from typing import Dict, List

class ChatRepository(ABC):
    @abstractmethod
    def chat(self, model: str, prompt: str, user_input: str, history: List[Dict[str, str]]) -> str:
        pass
    