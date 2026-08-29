from collections.abc import Sequence
from typing import Any

from ...application.dtos import CreateAgentInputDTO
from ...application.use_cases import (
    ChatWithAgentUseCase,
    CreateAgentUseCase,
    GetAgentConfigUseCase,
    GetSystemAvailableToolsUseCase,
)
from ...domain import Agent, BaseTool
from ...infra import (
    AvailableToolsRegistry,
    ChatAdapterFactory,
    LoggingConfig,
    create_logger,
)


class AgentComposer:
    """Composition root for agent-related use cases.

    The only place allowed to know about every layer at once: it builds the
    use cases and injects their concrete dependencies.
    """

    __logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def create_agent(
        provider: str,
        model: str,
        name: str | None = None,
        instructions: str | None = None,
        config: dict[str, Any] | None = None,
        tools: Sequence[str | BaseTool] | None = None,
        history_max_size: int = 10,
    ) -> Agent:
        """Create a new agent using the CreateAgentUseCase.

        Args:
            provider: The specific provider ("openai" or "ollama").
            model: The name of the AI model.
            name: The name of the agent (optional).
            instructions: The agent's instructions (optional).
            config: Extra agent configurations, such as `max_tokens` and `temperature` (optional).
            tools: Tool names or instances available to the agent (optional).
            history_max_size: The maximum history size (default: 10).

        Returns:
            A new agent instance.

        """
        AgentComposer.__logger.info(
            'Composing agent creation - Provider: %s, Model: %s, Name: %s',
            provider,
            model,
            name,
        )

        if config is None:
            config = {}

        AgentComposer.__logger.debug(
            'Agent parameters - Tools: %s, History max size: %s, Config keys: %s',
            len(tools) if tools else 0,
            history_max_size,
            list(config.keys()) if isinstance(config, dict) else 'invalid',
        )

        input_dto = CreateAgentInputDTO(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            tools=tools,
            history_max_size=history_max_size,
        )

        use_case = CreateAgentUseCase(
            tool_registry=AvailableToolsRegistry(),
            logger=create_logger(__name__),
        )
        agent = use_case.execute(input_dto)

        AgentComposer.__logger.info(
            'Agent composed successfully - Name: %s', agent.name
        )
        return agent

    @staticmethod
    def create_chat_use_case(provider: str) -> ChatWithAgentUseCase:
        """Create the ChatWithAgentUseCase with its dependencies injected.

        Args:
            provider: The specific provider ("openai" or "ollama").

        Returns:
            A configured ChatWithAgentUseCase.

        """
        AgentComposer.__logger.debug(
            'Composing chat use case - Provider: %s', provider
        )

        chat_adapter = ChatAdapterFactory.create(provider)
        use_case = ChatWithAgentUseCase(
            chat_repository=chat_adapter,
            logger=create_logger(__name__),
        )

        AgentComposer.__logger.debug('Chat use case composed successfully')
        return use_case

    @staticmethod
    def create_get_config_use_case() -> GetAgentConfigUseCase:
        """Create the GetAgentConfigUseCase.

        Returns:
            A configured GetAgentConfigUseCase.

        """
        AgentComposer.__logger.debug('Composing get config use case')
        return GetAgentConfigUseCase(logger=create_logger(__name__))

    @staticmethod
    def create_get_system_available_tools_use_case() -> (
        GetSystemAvailableToolsUseCase
    ):
        """Create the GetSystemAvailableToolsUseCase.

        This use case returns only system tools provided by the framework.

        Returns:
            A configured GetSystemAvailableToolsUseCase.

        """
        AgentComposer.__logger.debug(
            'Composing get system available tools use case'
        )
        return GetSystemAvailableToolsUseCase(
            tool_registry=AvailableToolsRegistry(),
            logger=create_logger(__name__),
        )
