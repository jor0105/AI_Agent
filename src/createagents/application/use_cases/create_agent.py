from collections.abc import Sequence

from ...domain import (
    Agent,
    BaseTool,
    History,
    InvalidAgentConfigException,
    InvalidBaseToolException,
    LoggerInterface,
    NullLogger,
)
from ..dtos import CreateAgentInputDTO
from ..interfaces import ToolRegistry


class CreateAgentUseCase:
    """Use Case for creating a new agent instance."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        logger: LoggerInterface | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            tool_registry: Port used to resolve tool names into instances.
            logger: Optional logger injected by the composition root.

        """
        self.__tool_registry = tool_registry
        self.__logger = logger or NullLogger()

    def execute(self, input_dto: CreateAgentInputDTO) -> Agent:
        """Create a new agent with the provided configurations.

        Args:
            input_dto: DTO with the data for agent creation.

        Returns:
            A new instance of the configured agent.

        Raises:
            InvalidAgentConfigException: If the input data is invalid.
            InvalidBaseToolException: If a tool name is not registered.
            InvalidProviderException: If the provider is not supported.
            UnsupportedConfigException: If a configuration is not supported.
            InvalidConfigTypeException: If a configuration type is invalid.

        """
        self.__logger.info(
            'Creating new agent - Provider: %s, Model: %s',
            input_dto.provider,
            input_dto.model,
        )
        self.__logger.debug(
            'Agent configuration - Name: %s, Tools: %s, History max size: %s',
            input_dto.name,
            len(input_dto.tools) if input_dto.tools else 0,
            input_dto.history_max_size,
        )

        try:
            input_dto.validate()
            self.__logger.debug('Input DTO validated successfully')
        except ValueError as e:
            self.__logger.exception('Validation error in input DTO')
            raise InvalidAgentConfigException('input_dto', str(e)) from e

        agent = Agent(
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=input_dto.instructions,
            config=input_dto.config,
            tools=self.__resolve_tools(input_dto.tools),
            history=History(max_size=input_dto.history_max_size),
        )

        self.__logger.info(
            'Agent created successfully - Name: %s, Provider: %s, Model: %s',
            agent.name,
            agent.provider,
            agent.model,
        )

        return agent

    def __resolve_tools(
        self, tools: Sequence[str | BaseTool] | None
    ) -> list[BaseTool] | None:
        """Turn every tool reference into a concrete `BaseTool` instance.

        Args:
            tools: Registered tool names, `BaseTool` instances, or None.

        Returns:
            The resolved tools, or None when the agent declares none.

        Raises:
            InvalidBaseToolException: If a name is not in the registry.

        """
        if tools is None:
            return None

        resolved: list[BaseTool] = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                resolved.append(tool)
                continue

            instance = self.__tool_registry.get_tool_instance(tool)
            if instance is None:
                self.__logger.error("Unknown tool requested: '%s'", tool)
                raise InvalidBaseToolException(tool)
            resolved.append(instance)

        return resolved
