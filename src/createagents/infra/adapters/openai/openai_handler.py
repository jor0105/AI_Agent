import time
from typing import Any, ClassVar

from ....domain import BaseTool, ChatException, ChatMetrics
from ...config import (
    DEFAULT_MAX_TOOL_ITERATIONS,
    EnvironmentConfig,
    LoggingConfig,
)
from ..common import OpenAIMetricsRecorder, ToolSession
from .openai_client import OpenAIClient
from .openai_tool_invoker import run_tool_calls
from .tool_call_parser import ToolCallParser
from .tool_schema_formatter import ToolSchemaFormatter


class OpenAIHandler:
    """Handles tool execution loop for OpenAI."""

    #: Maps a failure class to the sentence used in its log record and in the
    #: `ChatException` raised to the caller. Ordered from most to least
    #: specific; the first matching entry wins.
    __FAILURE_REASONS: ClassVar[
        tuple[tuple[type[Exception] | tuple[type[Exception], ...], str], ...]
    ] = (
        (AttributeError, 'Error accessing OpenAI response'),
        (IndexError, 'OpenAI response has an unexpected format'),
        (
            (ValueError, TypeError, KeyError),
            'Data error communicating with OpenAI',
        ),
    )
    __DEFAULT_FAILURE_REASON = 'Error communicating with OpenAI'

    def __init__(
        self,
        client: OpenAIClient,
        metrics_list: list[ChatMetrics] | None = None,
    ) -> None:
        """Initialize the handler.

        Args:
            client: Transport used to reach the OpenAI Responses API.
            metrics_list: Optional shared list to append metrics to.

        """
        self.__client = client
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics_recorder = OpenAIMetricsRecorder(metrics_list)
        self.__max_tool_iterations = EnvironmentConfig.get_int_env(
            'OPENAI_MAX_TOOL_ITERATIONS', DEFAULT_MAX_TOOL_ITERATIONS
        )

    async def execute_tool_loop(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> str:
        """Execute the tool calling loop.

        Args:
            model: The name of the model.
            instructions: System instructions, or None.
            messages: The conversation to send, extended in place with any
                tool calls and their results.
            config: Internal AI configuration.
            tools: Tools the agent may call, or None.

        Returns:
            The model's final answer.

        Raises:
            ChatException: If the model requests tools the agent does not
                have, returns an empty answer, exhausts the iteration budget,
                or the call fails.

        """
        start_time = time.time()
        session = ToolSession.prepare(
            tools,
            ToolSchemaFormatter.format_tools_for_responses_api,
            self.__logger,
            f'{__name__}.ToolExecutor',
        )

        iteration = 0
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    'OpenAI tool calling iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )
                self.__logger.debug(
                    'Current message history size: %s', len(messages)
                )

                response_api = await self.__client.call_api(
                    model, instructions, messages, config, session.schemas
                )

                if ToolCallParser.has_tool_calls(response_api):
                    self.__logger.info('Tool calls detected in response')

                    if session.executor is None:
                        self.__logger.error(
                            'Tool calls detected but no tools were provided'
                        )
                        raise ChatException(
                            'Tool calls detected but no tools were provided '
                            'to the agent'
                        )

                    await run_tool_calls(
                        response_api,
                        messages,
                        session.executor,
                        self.__logger,
                    )
                    continue

                content: str = response_api.output_text
                if not content:
                    self.__logger.warning('OpenAI returned an empty response.')
                    raise ChatException('OpenAI returned an empty response.')

                self.__metrics_recorder.record_success_metrics(
                    model, start_time, response_api
                )

                self.__logger.debug(
                    'Response (first 100 chars): %s...', content[:100]
                )

                return content

            self.__logger.warning(
                'Max tool iterations (%s) reached', self.__max_tool_iterations
            )
            raise ChatException(
                f'Max tool calling iterations '
                f'({self.__max_tool_iterations}) exceeded'
            )

        except ChatException:
            self.__metrics_recorder.record_error_metrics(
                model, start_time, 'OpenAI chat error'
            )
            raise
        except Exception as e:
            reason = self.__failure_reason(e)
            self.__metrics_recorder.record_error_metrics(
                model, start_time, f'{reason}: {e!s}'
            )
            self.__logger.exception(reason)
            raise ChatException(f'{reason}: {e!s}', original_error=e) from e

    @classmethod
    def __failure_reason(cls, error: Exception) -> str:
        """Describe a failure in the terms the caller sees.

        Args:
            error: The exception that ended the loop.

        Returns:
            The sentence that prefixes both the log record and the message of
            the resulting `ChatException`.

        """
        for error_types, reason in cls.__FAILURE_REASONS:
            if isinstance(error, error_types):
                return reason
        return cls.__DEFAULT_FAILURE_REASON

    def get_metrics(self) -> list[ChatMetrics]:
        """Return the list of collected metrics."""
        return self.__metrics_recorder.get_metrics()
