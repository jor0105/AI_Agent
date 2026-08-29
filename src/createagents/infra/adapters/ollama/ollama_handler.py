import time
from typing import Any, Final

from ....domain import BaseTool, ChatException, ChatMetrics
from ...config import (
    DEFAULT_MAX_TOOL_ITERATIONS,
    EnvironmentConfig,
    LoggingConfig,
)
from ..common import OllamaMetricsRecorder, ToolSession
from .ollama_client import OllamaClient, OllamaMessage
from .ollama_tool_invoker import run_tool_calls
from .ollama_tool_schema_formatter import OllamaToolSchemaFormatter

#: How many blank answers in a row are tolerated before the handler stops
#: asking and falls back to summarising the tool output it already has.
MAX_EMPTY_RESPONSES: Final[int] = 2

#: Nudge sent after a single blank answer, asking the model to commit.
_FINAL_ANSWER_PROMPT: Final[str] = (
    'Based on the information gathered, please provide a final answer to '
    'the original question.'
)

#: How many tool results the fallback summary quotes, and how much of each.
_SUMMARY_MAX_RESULTS: Final[int] = 3
_SUMMARY_MAX_CHARS: Final[int] = 500


class OllamaHandler:
    """Handles tool execution loop for Ollama."""

    def __init__(
        self,
        client: OllamaClient,
        metrics_list: list[ChatMetrics] | None = None,
    ) -> None:
        """Initialize the handler.

        Args:
            client: Transport used to reach the Ollama chat API.
            metrics_list: Optional shared list to append metrics to.

        """
        self.__client = client
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics_recorder = OllamaMetricsRecorder(metrics_list)
        self.__max_tool_iterations = EnvironmentConfig.get_int_env(
            'OLLAMA_MAX_TOOL_ITERATIONS', DEFAULT_MAX_TOOL_ITERATIONS
        )

    async def execute_tool_loop(
        self,
        model: str,
        messages: list[OllamaMessage],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> str:
        """Execute the tool calling loop.

        Args:
            model: The name of the model.
            messages: The conversation to send, extended in place with any
                tool calls and their results.
            config: Internal AI configuration.
            tools: Tools the agent may call, or None.

        Returns:
            The model's final answer.

        Raises:
            ChatException: If the model requests tools the agent does not
                have, keeps answering blank, or exhausts the iteration budget.

        """
        start_time = time.time()
        session = ToolSession.prepare(
            tools,
            OllamaToolSchemaFormatter.format_tools_for_ollama,
            self.__logger,
            f'{__name__}.ToolExecutor',
        )

        iteration = 0
        final_response = None
        empty_response_count = 0
        response_api = None

        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    'Ollama tool calling iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )

                response_api = await self.__client.call_api(
                    model, messages, config, session.schemas
                )

                assistant_turn = response_api.message
                if getattr(assistant_turn, 'tool_calls', None):
                    if session.executor is None:
                        self.__logger.error(
                            'Tool calls detected but no tools were provided'
                        )
                        raise ChatException(
                            'Tool calls detected but no tools were provided '
                            'to the agent'
                        )

                    await run_tool_calls(
                        assistant_turn,
                        messages,
                        session.executor,
                        self.__logger,
                    )
                    continue

                content = assistant_turn.content
                if content:
                    final_response = content
                    break

                empty_response_count += 1
                if empty_response_count >= MAX_EMPTY_RESPONSES:
                    summary = self.__summarize_tool_results(messages)
                    if summary is None:
                        raise ChatException(
                            'Ollama returned multiple empty responses.'
                        )
                    final_response = summary
                    break

                response_api = await self.__ask_for_final_answer(
                    model, messages, config
                )
                content = response_api.message.content
                if content:
                    final_response = content
                    break

            if final_response is None:
                raise ChatException(
                    f'Max tool calling iterations '
                    f'({self.__max_tool_iterations}) exceeded'
                )

            self.__metrics_recorder.record_success_metrics(
                model, start_time, response_api
            )
            return final_response

        except Exception as e:
            self.__metrics_recorder.record_error_metrics(model, start_time, e)
            raise

    async def __ask_for_final_answer(
        self,
        model: str,
        messages: list[OllamaMessage],
        config: dict[str, Any] | None,
    ) -> Any:
        """Re-ask without tools after the model returned a blank answer.

        The nudge goes to a copy of the conversation so a model that answers
        properly this time does not inherit the prompt on later turns.

        Args:
            model: The name of the model.
            messages: The conversation so far, left unchanged.
            config: Internal AI configuration.

        Returns:
            The retry response.

        """
        retry_messages = [
            *messages,
            {'role': 'user', 'content': _FINAL_ANSWER_PROMPT},
        ]
        return await self.__client.call_api(
            model, retry_messages, config, None
        )

    def __summarize_tool_results(
        self, messages: list[OllamaMessage]
    ) -> str | None:
        """Build an answer out of the tool output already collected.

        Used as a last resort when the model keeps returning nothing despite
        having usable tool results in context.

        Args:
            messages: The conversation, scanned for `tool` messages.

        Returns:
            The summary, or None when no tool produced any output.

        """
        try:
            tool_results = [
                f'From {message.get("tool_name", "unknown")}: '
                f'{message.get("content", "")[:_SUMMARY_MAX_CHARS]}'
                for message in messages
                if isinstance(message, dict)
                and message.get('role') == 'tool'
                and message.get('content')
            ]

            if not tool_results:
                return None

            return 'Based on the gathered information:\n\n' + '\n\n'.join(
                tool_results[:_SUMMARY_MAX_RESULTS]
            )
        except Exception:
            self.__logger.exception('Error formatting tool response')
            return None

    def get_metrics(self) -> list[ChatMetrics]:
        """Return the list of collected metrics."""
        return self.__metrics_recorder.get_metrics()
