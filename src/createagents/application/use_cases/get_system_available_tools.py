from ...domain import LoggerInterface, NullLogger
from ..interfaces import ToolRegistry


class GetSystemAvailableToolsUseCase:
    """Use case for retrieving system tools available in the AI Agent framework.

    System tools are built-in tools provided by the framework that are always
    available and can be added to any agent.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        logger: LoggerInterface | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            tool_registry: Port that exposes the framework's tool catalog.
            logger: Optional logger injected by the composition root.

        """
        self.__tool_registry = tool_registry
        self.__logger = logger or NullLogger()

    def execute(self) -> dict[str, str]:
        """Return a dictionary of available system tools.

        System tools are built-in tools provided by the AI Agent framework.

        Returns:
            Dict[str, str]: Dictionary mapping system tool names to descriptions.

        """
        self.__logger.debug('Retrieving available system tools.')
        system_tools: dict[str, str] = self.__tool_registry.get_system_tools()
        self.__logger.info('Retrieved %s system tool(s).', len(system_tools))
        return system_tools
