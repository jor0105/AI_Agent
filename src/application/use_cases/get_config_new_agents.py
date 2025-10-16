from src.application.dtos import AgentConfigOutputDTO
from src.domain.entities.agent_domain import Agent


class GetAgentConfigUseCase:
    """Use Case para obter as configurações de um agente."""

    def execute(self, agent: Agent) -> AgentConfigOutputDTO:
        """
        Retorna as configurações do agente em formato de DTO.

        Args:
            agent: Instância do agente

        Returns:
            AgentConfigOutputDTO: DTO com as configurações do agente
        """
        return AgentConfigOutputDTO(
            provider=agent.provider,
            model=agent.model,
            name=agent.name,
            instructions=agent.instructions,
            history=agent.history.to_dict_list(),  # Converte History para list[dict]
        )
