from collections.abc import AsyncGenerator, Sequence
from typing import Any

from ...application.dtos import ChatInputDTO, StreamingResponseDTO
from ...application.use_cases import (
    ChatWithAgentUseCase,
    GetAgentConfigUseCase,
    GetSystemAvailableToolsUseCase,
)
from ...domain import Agent, BaseTool, ChatMetrics
from ...infra import LoggingConfig, MetricsCollector
from ..composers import AgentComposer


class CreateAgent:
    """The application layer controller for interacting with AI agents.

    It is responsibility for coordinating requests and responses.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        name: str | None = None,
        instructions: str | None = None,
        config: dict[str, Any] | None = None,
        tools: Sequence[str | BaseTool] | None = None,
        history_max_size: int = 10,
    ) -> None:
        """Initializes the controller by creating an agent and its dependencies.

        Args:
            provider: The specific provider ("openai" or "ollama"), which
                defines which API to use.
            model: The name of the AI model.
            name: The name of the agent (optional).
            instructions: The agent's instructions or prompt (optional).
            config: Extra agent configurations, such as `max_tokens` and
                `temperature` (optional).
            tools: Tools the agent may call, given as registered system tool
                names or `BaseTool` instances (optional).
            history_max_size: The maximum history size (default: 10).
        """
        self.__logger = LoggingConfig.get_logger(__name__)

        self.__logger.info(
            'Initializing CreateAgent controller - Provider: %s, Model: %s, Name: %s',
            provider,
            model,
            name,
        )

        self.__agent: Agent = AgentComposer.create_agent(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            tools=tools,
            history_max_size=history_max_size,
        )

        self.__chat_use_case: ChatWithAgentUseCase = (
            AgentComposer.create_chat_use_case(provider=provider)
        )
        self.__get_config_use_case: GetAgentConfigUseCase = (
            AgentComposer.create_get_config_use_case()
        )
        self.__get_system_tools_use_case: GetSystemAvailableToolsUseCase = (
            AgentComposer.create_get_system_available_tools_use_case()
        )

        self.__logger.info(
            'CreateAgent controller initialized successfully - Agent: %s',
            self.__agent.name,
        )

    async def chat(
        self,
        message: str,
    ) -> str | StreamingResponseDTO:
        """Sends a message to the agent and returns the response.

        The response appears token-by-token in real-time when stream=True is configured,
        or as a complete response when stream=False (default).

        Args:
            message: The user's message.

        Returns:
            Union[str, StreamingResponseDTO]: The agent's response.
                Returns str for normal responses, or StreamingResponseDTO for streaming
                (which behaves like str when printed).

        Example:
            >>> agent = CreateAgent(provider="openai", model="gpt-5-nano")
            >>> print(await agent.chat("Hello!"))  # Works seamlessly with or without streaming
        """
        self.__logger.debug(
            'Chat request received - Message length: %s chars', len(message)
        )

        input_dto = ChatInputDTO(
            message=message,
        )
        result = await self.__chat_use_case.execute(self.__agent, input_dto)

        # If result is an AsyncGenerator (streaming mode), wrap in StreamingResponseDTO
        if isinstance(result, AsyncGenerator):
            self.__logger.debug(
                'Chat response: streaming mode (AsyncGenerator)'
            )
            return StreamingResponseDTO(result)

        # Otherwise it's a ChatOutputDTO, extract the response
        self.__logger.debug(
            'Chat response generated - Response length: %s chars',
            len(result.response),
        )

        response: str = result.response

        return response

    def get_configs(self) -> dict[str, Any]:
        """Returns the agent's configurations.

        Returns:
            A dictionary containing the agent's configurations.
        """
        self.__logger.debug('Retrieving agent configurations')
        output_dto = self.__get_config_use_case.execute(self.__agent)

        output_dict: dict[str, Any] = output_dto.to_dict()

        return output_dict

    def get_all_available_tools(self) -> dict[str, str]:
        """Return a dict of all available tools for THIS agent (system + agent-specific).

        This method returns:
        1. System tools (built-in tools like CurrentDateTool, ReadLocalFileTool)
        2. Agent-specific tools (custom tools added when this agent was created)

        Note: System tools are not duplicated. If an agent has a system tool
        in its tools list, it won't be added twice.

        Returns:
            A dict of all tool names and descriptions available for this agent.
        """
        self.__logger.debug(
            'Retrieving all tools for this agent (system + agent-specific)'
        )

        all_tools: dict[str, str] = self.__get_system_tools_use_case.execute()

        for tool in self.__agent.tools or ():
            all_tools.setdefault(tool.name.lower(), tool.description)

        self.__logger.info(
            "Retrieved %s tool(s) for agent '%s'",
            len(all_tools),
            self.__agent.name,
        )
        return all_tools

    def get_system_available_tools(self) -> dict[str, str]:
        """Return a dict of system tools only.

        System tools are built-in tools provided by the AI Agent framework
        that are always available and can be added to any agent.

        Returns:
            A dict of system tool names and descriptions.
        """
        self.__logger.debug('Retrieving system available tools')
        output_dto: dict[str, str] = self.__get_system_tools_use_case.execute()
        return output_dto

    def clear_history(self) -> None:
        """Clears the agent's history."""
        history_size = len(self.__agent.history)
        self.__agent.clear_history()
        self.__logger.info(
            'Agent history cleared - Removed %s message(s)', history_size
        )

    def get_metrics(self) -> list[ChatMetrics]:
        """Returns the performance metrics of the chat adapter.

        Returns:
            A list of metrics collected during interactions.
        """
        metrics: list[ChatMetrics] = self.__chat_use_case.get_metrics()
        self.__logger.debug('Retrieved %s metric(s)', len(metrics))
        return metrics

    def export_metrics_json(self, filepath: str | None = None) -> str:
        """Exports metrics in JSON format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A JSON string with the metrics.
        """
        self.__logger.debug(
            'Exporting metrics to JSON - Filepath: %s',
            filepath or 'None (return string)',
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        json_result: str = collector.export_json(filepath)

        if filepath:
            self.__logger.info('Metrics exported to JSON file: %s', filepath)
        else:
            self.__logger.debug('Metrics exported as JSON string')

        return json_result

    def export_metrics_prometheus(self, filepath: str | None = None) -> str:
        """Exports metrics in Prometheus format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A string in Prometheus format with the metrics.
        """
        self.__logger.debug(
            'Exporting metrics to Prometheus - Filepath: %s',
            filepath or 'None (return string)',
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        prometheus_text: str = collector.export_prometheus()

        if filepath:
            collector.export_prometheus_to_file(filepath)
            self.__logger.info(
                'Metrics exported to Prometheus file: %s', filepath
            )
        else:
            self.__logger.debug('Metrics exported as Prometheus string')

        return prometheus_text

    def start_cli(self) -> None:
        """Start interactive CLI chat session.

        This method launches a terminal-based interactive chat interface
        using the presentation layer's CLI application.

        Example:
            >>> agent = CreateAgent(provider="openai", model="gpt-4")
            >>> agent.start_cli()  # Starts interactive chat
        """
        # Keep the terminal stack lazy for consumers that never open a CLI.
        from ...presentation.cli import ChatCLIApplication

        self.__logger.info(
            'Starting CLI application for agent: %s', self.__agent.name
        )

        cli_app = ChatCLIApplication(agent=self)
        cli_app.run()

        self.__logger.info('CLI application ended')
