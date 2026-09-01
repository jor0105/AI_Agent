import json
from typing import Any

from ...config import LoggingConfig


class ToolCallParser:
    """Parser for OpenAI Responses API tool calls.

    This class is responsible for extracting and parsing tool call information
    from OpenAI Responses API responses.

    OpenAI Responses API returns tool calls in the response.output list:
    ```python
    response.output = [
        {
            "id": "fc_abc123",
            "call_id": "call_abc123",
            "type": "function_call",
            "name": "get_weather",
            "arguments": '{"location": "Paris"}'
        }
    ]
    ```
    """

    _logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def has_tool_calls(response: Any) -> bool:
        """Check if the response contains tool calls.

        Args:
            response: OpenAI Responses API response object.

        Returns:
            True if tool calls are present, False otherwise.

        """
        try:
            if not hasattr(response, 'output') or not response.output:
                ToolCallParser._logger.debug(
                    'Response has no output attribute or output is empty'
                )
                return False

            # Check if any item in output has type "function_call"
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'function_call':
                    ToolCallParser._logger.debug(
                        'Tool calls detected in response'
                    )
                    return True

            ToolCallParser._logger.debug('No tool calls found in response')
            return False
        except (AttributeError, TypeError) as e:
            ToolCallParser._logger.warning(
                'Error checking for tool calls: %s', e
            )
            return False

    @staticmethod
    def extract_tool_calls(response: Any) -> list[dict[str, Any]]:
        """Extract tool calls from OpenAI Responses API response.

        Args:
            response: OpenAI Responses API response object.

        Returns:
            List of tool call dictionaries with 'id', 'name', and 'arguments'
            keys. Calls whose arguments cannot be parsed also include an
            'error' key so the caller can return a function-call output to the
            API. Returns an empty list if no tool calls are present.

        Example:
            ```python
            [
                {
                    "id": "call_abc123",
                    "name": "get_weather",
                    "arguments": {"location": "Paris"}
                }
            ]
            ```

        """
        if not ToolCallParser.has_tool_calls(response):
            ToolCallParser._logger.debug('No tool calls to extract')
            return []

        ToolCallParser._logger.debug('Extracting tool calls from response')
        tool_calls = []

        for item in response.output:
            if not hasattr(item, 'type') or item.type != 'function_call':
                continue

            try:
                # Parse arguments from JSON string
                arguments_str = item.arguments
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str)
                else:
                    arguments = arguments_str
                if not isinstance(arguments, dict):
                    raise TypeError(
                        'tool call arguments must be a JSON object'
                    )

                tool_call = {
                    'id': item.call_id,  # Responses API uses call_id
                    'name': item.name,
                    'arguments': arguments,
                }
                tool_calls.append(tool_call)
                ToolCallParser._logger.debug(
                    'Extracted tool call: %s with call_id: %s',
                    item.name,
                    item.call_id,
                )

            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                ToolCallParser._logger.error(
                    'Failed to parse tool call: %s', e, exc_info=True
                )
                call_id = getattr(item, 'call_id', None)
                if call_id:
                    tool_calls.append(
                        {
                            'id': call_id,
                            'name': getattr(item, 'name', 'unknown'),
                            'arguments': {},
                            'error': (
                                'The tool call arguments could not be parsed: '
                                f'{e!s}'
                            ),
                        }
                    )

        ToolCallParser._logger.info(
            'Extracted %s tool call(s)', len(tool_calls)
        )
        return tool_calls

    @staticmethod
    def format_tool_results_for_llm(
        tool_call_id: str, tool_name: str, result: str
    ) -> dict[str, Any]:
        """Format tool execution result for sending back to OpenAI Responses API.

        Args:
            tool_call_id: The call_id of the tool call (from the original response).
            tool_name: Name of the tool that was executed.
            result: The result of the tool execution.

        Returns:
            A dictionary formatted for Responses API's input array.

        Example:
            ```python
            {
                "type": "function_call_output",
                "call_id": "call_abc123",
                "output": "Weather in Paris: 15°C"
            }
            ```

        """
        ToolCallParser._logger.debug(
            "Formatting tool result for '%s' with call_id '%s'",
            tool_name,
            tool_call_id,
        )

        formatted = {
            'type': 'function_call_output',
            'call_id': tool_call_id,
            'output': str(result),
        }

        ToolCallParser._logger.debug(
            'Formatted tool result (length: %s chars)', len(str(result))
        )
        return formatted

    @staticmethod
    def get_assistant_message_with_tool_calls(
        response: Any,
    ) -> list[dict[str, Any]] | None:
        """Extract the output items from response for adding to input history.

        For Responses API, we need to append specific output items to maintain context.
        We only include 'reasoning' and 'function_call' types,
        filtering out extra fields.

        Args:
            response: OpenAI Responses API response object.

        Returns:
            List of output items (cleaned), or None if not available.

        """
        if not ToolCallParser.has_tool_calls(response):
            ToolCallParser._logger.debug(
                'No tool calls in response, skipping extraction'
            )
            return None

        try:
            if not hasattr(response, 'output') or not response.output:
                ToolCallParser._logger.warning(
                    'Response has no output for assistant message'
                )
                return None

            ToolCallParser._logger.debug(
                'Extracting assistant message with tool calls'
            )

            # Convert to dict format for messages, keeping only necessary fields
            # (broken into multiple lines for lint compliance)
            output_items = []
            for item in response.output:
                item_type = getattr(item, 'type', None)

                # Only include reasoning and function_call types
                if item_type == 'reasoning':
                    output_items.append(
                        {
                            'type': 'reasoning',
                            'id': getattr(item, 'id', None),
                            'summary': getattr(item, 'summary', []),
                        }
                    )
                    ToolCallParser._logger.debug(
                        'Included reasoning item in assistant message'
                    )
                elif item_type == 'function_call':
                    output_items.append(
                        {
                            'type': 'function_call',
                            'id': getattr(item, 'id', None),
                            'call_id': getattr(item, 'call_id', None),
                            'name': getattr(item, 'name', None),
                            'arguments': getattr(item, 'arguments', None),
                        }
                    )
                    ToolCallParser._logger.debug(
                        "Included function_call item for '%s'",
                        getattr(item, 'name', 'unknown'),
                    )

            if output_items:
                ToolCallParser._logger.info(
                    'Extracted %s output item(s) for assistant message',
                    len(output_items),
                )
            else:
                ToolCallParser._logger.warning(
                    'No valid output items found in response'
                )

            return output_items if output_items else None

        except (AttributeError, TypeError) as e:
            ToolCallParser._logger.error(
                'Error extracting assistant message with tool calls: %s',
                e,
                exc_info=True,
            )
            return None
