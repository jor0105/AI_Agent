from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DomainAIAgent:
    model: str
    name: str
    prompt: str
    history: List[Dict[str, str]] = field(default_factory=list)
