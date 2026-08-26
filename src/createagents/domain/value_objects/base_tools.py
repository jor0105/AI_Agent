from abc import ABC, abstractmethod
from typing import Any, ClassVar


class BaseTool(ABC):
    """Base class for all tools that the agent can use.

    This class defines the contract that all tools must follow.
    Tools are capabilities that the AI agent can invoke to perform
    specific tasks (e.g., web search, calculations, API calls).

    Attributes:
        name (str): Unique identifier for the tool (e.g., 'web_search').
        description (str): Clear description of what the tool does and when to use it.
                          This description is used by the LLM to decide when to invoke the tool.
        parameters (dict): JSON Schema describing the tool's parameters.
                          Default is an empty object schema.

    Subclasses must:
        1. Set class attributes `name` and `description`
        2. Optionally set `parameters` with a JSON Schema
        3. Implement the `execute` method with the tool's logic

    Example:
        ```python
        class WordCountTool(BaseTool):
            name = "word_count"
            description = "Counts the number of words in a text"
            parameters = {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to count words from",
                    }
                },
                "required": ["text"],
            }

            def execute(self, text: str) -> str:
                return str(len(text.split()))
        ```
    """

    name: str = 'base_tool'
    description: str = 'Base tool description (should be overridden)'

    parameters: ClassVar[dict[str, Any]] = {
        'type': 'object',
        'properties': {},
    }

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool's main functionality.

        This method must be implemented by all subclasses.

        Args:
            *args: Positional arguments specific to the tool.
            **kwargs: Keyword arguments specific to the tool.

        Returns:
            The result of the tool execution (typically a string).
        """

    def get_schema(self) -> dict[str, Any]:
        """Return a generic schema describing the tool.

        This method returns a provider-agnostic schema that contains
        all necessary information about the tool. Infrastructure adapters
        can transform this schema to their specific format.

        Returns:
            A dictionary with 'name', 'description', and 'parameters' keys.

        Example:
            ```python
            {
                "name": "web_search",
                "description": "Search the web for information",
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
            ```
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
        }
