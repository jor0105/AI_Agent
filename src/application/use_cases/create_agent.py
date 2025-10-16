from src.application.dtos import CreateAgentInputDTO
from src.domain.entities.agent_domain import Agent
from src.domain.exceptions import InvalidAgentConfigException
from src.domain.value_objects import History


class CreateAgentUseCase:
    """Use Case para criar uma nova instância de agente."""

    def execute(self, input_dto: CreateAgentInputDTO) -> Agent:
        """
        Cria um novo agente com as configurações fornecidas.

        Args:
            input_dto: DTO com os dados para criação do agente

        Returns:
            Agent: Nova instância do agente configurado

        Raises:
            InvalidAgentConfigException: Se os dados de entrada forem inválidos
        """
        try:
            input_dto.validate()

            agent = Agent(
                provider=input_dto.provider,
                model=input_dto.model,
                name=input_dto.name,
                instructions=input_dto.instructions,
                history=History(max_size=input_dto.history_max_size),
            )

            return agent

        except ValueError as e:
            raise InvalidAgentConfigException("input_dto", str(e))
