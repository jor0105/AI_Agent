"""Execution of the tool calls in one OpenAI Responses API turn.

The buffered handler and the streaming handler reach this point with the same
object -- a completed response -- and owe the model the same thing: the
assistant's own output items echoed back, followed by one result item per
call. That sequence lives here so both paths cannot drift apart.
"""

import logging
from typing import Any

from ....domain import ToolExecutor
from .tool_call_parser import ToolCallParser


async def run_tool_calls(
    response: Any,
    messages: list[dict[str, Any]],
    executor: ToolExecutor,
    logger: logging.Logger,
) -> None:
    """Run every tool the model asked for and extend `messages` in place.

    Args:
        response: The completed Responses API object carrying the tool calls.
        messages: The conversation sent to the model, extended in place with
            the assistant's output items and each tool result.
        executor: Executor holding the agent's tools.
        logger: Logger of the calling handler.

    """
    output_items = ToolCallParser.get_assistant_message_with_tool_calls(
        response
    )
    if output_items:
        messages.extend(output_items)

    tool_calls = ToolCallParser.extract_tool_calls(response)
    logger.info('Executing %s tool(s)', len(tool_calls))

    for tool_call in tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['arguments']

        logger.debug("Executing tool '%s' with args: %s", tool_name, tool_args)

        execution_result = await executor.execute_tool(tool_name, **tool_args)

        messages.append(
            ToolCallParser.format_tool_results_for_llm(
                tool_call_id=tool_call['id'],
                tool_name=tool_name,
                result=(
                    str(execution_result.result)
                    if execution_result.success
                    else str(execution_result.error)
                ),
            )
        )
