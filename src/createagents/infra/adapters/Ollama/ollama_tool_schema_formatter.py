from typing import Any

from ....domain import BaseTool
from ...config import LoggingConfig


class OllamaToolSchemaFormatter:
    """Formatter for Ollama native tool calling schemas.

    Converts BaseTool instances to Ollama's function calling format.

    Ollama expects tools in this format:
    ```python
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "Tool description",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
    ```
    """

    _logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def format_tools_for_ollama(tools: list[BaseTool]) -> list[dict[str, Any]]:
        """Convert BaseTool instances to Ollama's native tool format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of tool schemas in Ollama's format.

        Example:
            Input: [WebSearchTool()]
            Output: [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web...",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                },
                ...
            ]
        """
        if not tools:
            OllamaToolSchemaFormatter._logger.debug('No tools to format')
            return []

        formatted_tools = []
        for tool in tools:
            try:
                schema = tool.get_schema()

                # Convert to Ollama's native format
                ollama_tool = {
                    'type': 'function',
                    'function': {
                        'name': schema['name'],
                        'description': schema['description'],
                        'parameters': schema['parameters'],
                    },
                }

                formatted_tools.append(ollama_tool)
                OllamaToolSchemaFormatter._logger.debug(
                    "Formatted tool '%s' for Ollama", schema['name']
                )
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                OllamaToolSchemaFormatter._logger.error(
                    'Error formatting tool %s: %s', tool.name, e, exc_info=True
                )
                continue

        OllamaToolSchemaFormatter._logger.info(
            'Formatted %s tool(s) for Ollama native API', len(formatted_tools)
        )
        return formatted_tools
