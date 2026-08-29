from ...domain import Agent, LoggerInterface, NullLogger
from ..dtos import AgentConfigOutputDTO


class GetAgentConfigUseCase:
    """Use case for retrieving agent configurations."""

    def __init__(self, logger: LoggerInterface | None = None) -> None:
        """Initialize the use case.

        Args:
            logger: Optional logger injected by the composition root.

        """
        self.__logger = logger or NullLogger()

    def execute(self, agent: Agent) -> AgentConfigOutputDTO:
        """Return the agent's configurations as a DTO.

        Args:
            agent: The agent instance.

        Returns:
            A DTO containing the agent's configurations.

        """
        self.__logger.debug(
            'Retrieving configuration for agent - Name: %s, Provider: %s, Model: %s',
            agent.name,
            agent.provider,
            agent.model,
        )

        config_dto = AgentConfigOutputDTO(
            provider=agent.provider,
            model=agent.model,
            name=agent.name,
            instructions=agent.instructions,
            config=agent.config,
            tools=agent.tools,
            history=agent.history.to_dict_list(),
            history_max_size=agent.history.max_size,
        )

        self.__logger.debug(
            'Configuration retrieved - History size: %s/%s, Tools: %s',
            len(agent.history),
            agent.history.max_size,
            len(agent.tools) if agent.tools else 0,
        )

        return config_dto
