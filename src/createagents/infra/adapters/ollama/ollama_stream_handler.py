import time
from collections.abc import AsyncGenerator
from typing import Any

from ....domain import BaseTool, ChatException, ChatMetrics
from ...config import LoggingConfig
from ..common import (
    BaseStreamHandler,
    StreamUsageTotals,
    ToolSession,
    nanoseconds_to_milliseconds,
)
from .ollama_client import OllamaClient, OllamaMessage
from .ollama_tool_invoker import run_tool_calls
from .ollama_tool_schema_formatter import OllamaToolSchemaFormatter

#: Ollama duration fields, paired with the `StreamUsageTotals` field each one
#: feeds once converted from nanoseconds.
_DURATION_FIELDS: tuple[tuple[str, str], ...] = (
    ('load_duration', 'load_duration_ms'),
    ('prompt_eval_duration', 'prompt_eval_duration_ms'),
    ('eval_duration', 'eval_duration_ms'),
)


class OllamaStreamHandler(BaseStreamHandler):
    """Handles streaming responses from Ollama with tool calling support."""

    def __init__(
        self,
        client: OllamaClient,
        metrics_list: list[ChatMetrics] | None = None,
    ) -> None:
        """Initialize the streaming handler.

        Args:
            client: Transport used to reach the Ollama chat API.
            metrics_list: Optional shared list to append metrics to.

        """
        super().__init__(
            logger=LoggingConfig.get_logger(__name__),
            max_iterations_env_var='OLLAMA_MAX_TOOL_ITERATIONS',
            metrics_list=metrics_list,
        )
        self.__client = client

    async def handle_stream(
        self,
        model: str,
        messages: list[OllamaMessage],
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
    ) -> AsyncGenerator[str, None]:
        """Yield tokens from the Ollama API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.

        Args:
            model: The name of the model.
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
            OllamaToolSchemaFormatter.format_tools_for_ollama,
            self._logger,
            f'{__name__}.ToolExecutor',
        )

        # Token counts accumulate across every iteration of a tool-calling
        # turn, so the metric covers the whole turn rather than the last call.
        totals = StreamUsageTotals()

        iteration = 0
        try:
            while iteration < self.max_tool_iterations:
                iteration += 1
                self._logger.info(
                    'Ollama streaming iteration %s/%s',
                    iteration,
                    self.max_tool_iterations,
                )

                stream_response = await self.__client.stream_api(
                    model, messages, config, session.schemas
                )

                has_yielded_content = False
                last_chunk = None
                tool_call_detected = False

                async for chunk in stream_response:
                    last_chunk = chunk
                    chunk_message = getattr(chunk, 'message', None)

                    # Stop reading as soon as a chunk carries tool calls;
                    # the rest of the stream cannot add anything useful.
                    if session.executor and getattr(
                        chunk_message, 'tool_calls', None
                    ):
                        tool_call_detected = True
                        self._logger.debug(
                            'Tool calls detected early in stream, will break'
                        )
                        break

                    token = getattr(chunk_message, 'content', None)
                    if token:
                        yield token
                        has_yielded_content = True

                # Ollama reports usage only on the final chunk of a stream.
                if last_chunk is not None:
                    self.__accumulate_usage(totals, last_chunk, iteration)

                assistant_turn = (
                    last_chunk.message if last_chunk is not None else None
                )
                if (
                    tool_call_detected
                    and session.executor
                    and getattr(assistant_turn, 'tool_calls', None)
                ):
                    self._logger.info('Tool calls detected, executing tools')
                    await run_tool_calls(
                        assistant_turn,
                        messages,
                        session.executor,
                        self._logger,
                    )
                    continue

                if has_yielded_content:
                    break

                if tool_call_detected:
                    self._logger.debug(
                        'Tool-only iteration, continuing to next'
                    )
                    continue

                self._logger.warning(
                    'No content yielded in streaming response'
                )
                break

            self.warn_if_iterations_exhausted(iteration)
            self.record_stream_success(model, start_time, totals, iteration)

        except Exception as e:
            self.record_stream_error(model, start_time, e)
            raise ChatException(
                f'Error during Ollama streaming: {e!s}', original_error=e
            ) from e

    def __accumulate_usage(
        self, totals: StreamUsageTotals, chunk: Any, iteration: int
    ) -> None:
        """Add the final chunk's token counts and durations to the totals.

        Args:
            totals: The turn's accumulated usage, updated in place.
            chunk: The last chunk seen in this iteration's stream.
            iteration: The iteration number, for the debug trace.

        """
        prompt_eval_count = getattr(chunk, 'prompt_eval_count', None)
        eval_count = getattr(chunk, 'eval_count', None)
        totals.add_tokens(prompt_eval_count, eval_count)

        for attribute, field_name in _DURATION_FIELDS:
            milliseconds = nanoseconds_to_milliseconds(
                getattr(chunk, attribute, None)
            )
            if milliseconds is not None:
                setattr(totals, field_name, milliseconds)

        self._logger.debug(
            'Iteration %s tokens - prompt: %s, completion: %s',
            iteration,
            prompt_eval_count,
            eval_count,
        )
