from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class AIAgent:
    model: str
    name: str
    prompt: str
    history: List[Dict[str, str]] = field(default_factory=list)
