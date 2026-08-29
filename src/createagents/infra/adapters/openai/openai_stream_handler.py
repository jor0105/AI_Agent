import time
from collections.abc import AsyncGenerator, Iterator
from typing import Any

from ....domain import BaseTool, ChatException, ChatMetrics
from ...config import LoggingConfig
from ..common import BaseStreamHandler, StreamUsageTotals, ToolSession
from .openai_client import OpenAIClient
from .openai_tool_invoker import run_tool_calls
from .tool_call_parser import ToolCallParser
from .tool_schema_formatter import ToolSchemaFormatter


class OpenAIStreamHandler(BaseStreamHandler):
    """Handles streaming responses from OpenAI with tool calling support."""

    def __init__(
        self,
        client: OpenAIClient,
        metrics_list: list[ChatMetrics] | None = None,
    ) -> None:
        """Initialize the streaming handler.

        Args:
            client: Transport used to reach the OpenAI Responses API.
            metrics_list: Optional shared list to append metrics to.

        """
        super().__init__(
            logger=LoggingConfig.get_logger(__name__),
            max_iterations_env_var='OPENAI_MAX_TOOL_ITERATIONS',
            metrics_list=metrics_list,
        )
        self.__client = client

    async def handle_stream(
        self,
        model: str,
        instructions: str | None,
        messages: list[dict[str, str]],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> AsyncGenerator[str, None]:
        """Yield tokens from the OpenAI API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.

        Args:
            model: The name of the model.
            instructions: System instructions, or None.
            messages: The conversation to send, extended in place with any
                tool calls and their results.
            config: Internal AI configuration.
            tools: Tools the agent may call, or None.

        Yields:
            Each token as the provider emits it.

        Raises:
            ChatException: If the streaming call fails.

        """
        start_time = time.time()
        session = ToolSession.prepare(
            tools,
            ToolSchemaFormatter.format_tools_for_responses_api,
            self._logger,
            f'{__name__}.ToolExecutor',
        )

        self._logger.debug('Streaming mode enabled for OpenAI')

        # Token counts accumulate across every iteration of a tool-calling
        # turn, so the metric covers the whole turn rather than the last call.
        totals = StreamUsageTotals()

        iteration = 0
        try:
            while iteration < self.max_tool_iterations:
                iteration += 1
                self._logger.info(
                    'OpenAI streaming iteration %s/%s',
                    iteration,
                    self.max_tool_iterations,
                )

                stream_response = await self.__client.call_api(
                    model, instructions, messages, config, session.schemas
                )

                self._logger.debug(
                    'Streaming response received, iterating events'
                )

                full_response = None
                has_yielded_content = False

                async for event in stream_response:
                    token, completed = self._extract_stream_event(event)
                    if token:
                        yield token
                        has_yielded_content = True
                    if completed is not None:
                        full_response = completed

                if not full_response:
                    self._logger.warning(
                        'No response object received from stream'
                    )
                    break

                # Fall back to the completed response when no text delta
                # arrived, so a provider that skips deltas still produces
                # output instead of an empty stream.
                if not has_yielded_content:
                    for text in self.__texts_in(full_response):
                        yield text

                self.__accumulate_usage(totals, full_response, iteration)

                if session.executor and ToolCallParser.has_tool_calls(
                    full_response
                ):
                    await run_tool_calls(
                        full_response,
                        messages,
                        session.executor,
                        self._logger,
                    )
                    continue

                # Response complete, no tool calls - end stream
                break

            self.warn_if_iterations_exhausted(iteration)
            self.record_stream_success(model, start_time, totals, iteration)

        except Exception as e:
            self.record_stream_error(model, start_time, e)
            raise ChatException(
                f'Error during OpenAI streaming: {e!s}',
                original_error=e,
            ) from e

    @staticmethod
    def _extract_stream_event(event: Any) -> tuple[str | None, Any | None]:
        """Extract incremental token or completed response from a stream event.

        Args:
            event: An event emitted by the OpenAI streaming API.

        Returns:
            A tuple of (text_delta, completed_response).

        """
        event_type = getattr(event, 'type', None)
        if event_type == 'response.output_text.delta':
            return getattr(event, 'delta', None), None
        if event_type == 'response.content_part.added':
            content_part = getattr(event, 'content_part', None)
            return getattr(content_part, 'text', None), None
        if event_type == 'response.completed':
            return None, getattr(event, 'response', None)
        return None, None

    def __accumulate_usage(
        self, totals: StreamUsageTotals, response: Any, iteration: int
    ) -> None:
        """Add this iteration's token counts to the turn's running totals.

        Args:
            totals: The turn's accumulated usage, updated in place.
            response: The object from the `response.completed` event.
            iteration: The iteration number, for the debug trace.

        """
        usage = getattr(response, 'usage', None)
        if not usage:
            return

        prompt_tokens = getattr(usage, 'input_tokens', None)
        completion_tokens = getattr(usage, 'output_tokens', None)
        totals.add_tokens(prompt_tokens, completion_tokens)
        self._logger.debug(
            'Iteration %s tokens - prompt: %s, completion: %s',
            iteration,
            prompt_tokens,
            completion_tokens,
        )

    @staticmethod
    def __texts_in(response: Any) -> Iterator[str]:
        """Yield the assistant text carried by a completed response.

        The Responses API nests it as
        `output[] -> type 'message' -> content[] -> type 'output_text'`.

        Args:
            response: The object from the `response.completed` event.

        Yields:
            Each non-empty text part, in order.

        """
        for item in getattr(response, 'output', None) or ():
            if getattr(item, 'type', None) != 'message':
                continue
            for part in getattr(item, 'content', None) or ():
                if getattr(part, 'type', None) != 'output_text':
                    continue
                text = getattr(part, 'text', None)
                if text:
                    yield text
