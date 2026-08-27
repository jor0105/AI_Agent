from abc import ABC, abstractmethod

from ...domain import BaseTool


class ToolRegistry(ABC):
    """Port for reading the catalog of tools the framework can offer.

    Implemented in the infrastructure layer. Declared here so the use cases
    depend on this abstraction instead of a concrete registry.
    """

    @abstractmethod
    def get_system_tools(self) -> dict[str, str]:
        """Return built-in framework tools as `{name: description}`."""

    @abstractmethod
    def get_tool_instance(self, tool_name: str) -> BaseTool | None:
        """Return the tool registered under `tool_name`, or None.

        Args:
            tool_name: The registered tool name, matched case-insensitively.
        """
