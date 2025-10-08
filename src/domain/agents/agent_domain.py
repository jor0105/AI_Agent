from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DomainAIAgent:
    model: str
    name: str
    instructions: str
    history: List[Dict[str, str]] = field(default_factory=list)

    def update_history(self, entry: dict, max_history: int = 10) -> None:
        self.history.append(entry)
        self.history = self.history[-max_history:]
