from typing import Dict

from src.domain.agents.agent_domain import DomainAIAgent


class GetConfigNewAgentsUseCase:
    @staticmethod
    def execute(agent: DomainAIAgent) -> Dict:
        return {
            "Name": agent.name,
            "Model": agent.model,
            "Prompt": agent.instructions,
            "History": agent.history,
        }
