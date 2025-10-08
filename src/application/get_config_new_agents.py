from typing import Dict

from src.domain.Agents.agents import AIAgent


class GetConfigNewAgentUseCase:
    @staticmethod
    def execute(agent: AIAgent) -> Dict:
        return {
            "Name": agent.name,
            "Model": agent.model,
            "Prompt": agent.prompt,
            "History": agent.history,
        }
