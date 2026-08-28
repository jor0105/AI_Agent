"""Execution of the tool calls in one Ollama chat turn.

The buffered handler and the streaming handler both reach this point holding
the assistant turn that carries the calls, and owe the model the same thing:
that turn echoed back, followed by one `tool` message per call. That sequence
lives here so both paths cannot drift apart.
"""

import logging
from typing import Any

from ....domain import ToolExecutor
from .ollama_client import OllamaMessage


async def run_tool_calls(
    assistant_turn: Any,
    messages: list[OllamaMessage],
    executor: ToolExecutor,
    logger: logging.Logger,
) -> None:
    """Run every tool the model asked for and extend `messages` in place.

    Args:
        assistant_turn: The assistant message carrying `tool_calls`. It is
            echoed back verbatim so the model keeps the calls it just made in
            context.
        messages: The conversation sent to the model, extended in place.
        executor: Executor holding the agent's tools.
        logger: Logger of the calling handler.
    """
    tool_calls = assistant_turn.tool_calls
    messages.append(assistant_turn)

    logger.debug('Executing %s tool(s)', len(tool_calls))

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool_args = tool_call.function.arguments

        logger.debug("Executing tool '%s' with args: %s", tool_name, tool_args)

        execution_result = await executor.execute_tool(tool_name, **tool_args)

        messages.append(
            {
                'role': 'tool',
                'tool_name': tool_name,
                'content': (
                    str(execution_result.result)
                    if execution_result.success
                    else f'Error: {execution_result.error}'
                ),
            }
        )
