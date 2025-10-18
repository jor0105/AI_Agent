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
            InvalidProviderException: Se o provider não for suportado
            UnsupportedConfigException: Se uma config não for suportada
            InvalidConfigTypeException: Se o tipo de uma config for inválido
        """
        try:
            input_dto.validate()
        except ValueError as e:
            raise InvalidAgentConfigException("input_dto", str(e))

        agent = Agent(
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=input_dto.instructions,
            config=input_dto.config,
            history=History(max_size=input_dto.history_max_size),
        )

        return agent
