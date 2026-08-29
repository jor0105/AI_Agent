from typing import Any

from ....domain import BaseTool
from ...config import LoggingConfig


class ToolSchemaFormatter:
    """Formats tool schemas for the OpenAI Responses API.

    This class converts domain-level tool schemas into the specific format
    required by the Responses API, which is the only OpenAI surface this
    adapter calls.

    Responsibilities:
    - Transform generic tool schemas to the Responses API format
    - Ensure compliance with OpenAI's schema requirements
    - Keep provider-specific logic out of the domain layer
    """

    _logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def format_tool_for_responses_api(tool: BaseTool) -> dict[str, Any]:
        """Convert a tool to OpenAI Responses API format.

        Args:
            tool: A BaseTool instance from the domain layer.

        Returns:
            A dictionary formatted for Responses API's tools parameter.

        """
        schema = tool.get_schema()

        ToolSchemaFormatter._logger.debug(
            "Formatting tool '%s' for OpenAI Responses API", schema['name']
        )

        return {
            'type': 'function',
            'name': schema['name'],
            'description': schema['description'],
            'parameters': schema['parameters'],
        }

    @staticmethod
    def format_tools_for_responses_api(
        tools: list[BaseTool],
    ) -> list[dict[str, Any]]:
        """Convert multiple tools to OpenAI Responses API format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of dictionaries formatted for Responses API's tools parameter.

        """
        ToolSchemaFormatter._logger.info(
            'Formatting %s tool(s) for OpenAI Responses API', len(tools)
        )

        formatted = [
            ToolSchemaFormatter.format_tool_for_responses_api(tool)
            for tool in tools
        ]

        ToolSchemaFormatter._logger.debug(
            'Formatted tools: %s', [t['name'] for t in formatted]
        )

        return formatted
