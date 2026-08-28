from ....application.interfaces import ToolRegistry
from ....domain import BaseTool
from .available_tools import AvailableTools


class AvailableToolsRegistry(ToolRegistry):
    """Adapts the `AvailableTools` catalog to the application's port.

    `AvailableTools` is a class-level registry; this adapter gives the
    application layer an injectable instance to depend on instead.
    """

    def get_system_tools(self) -> dict[str, str]:
        """Return built-in framework tools as `{name: description}`."""
        return AvailableTools.get_system_tools()

    def get_tool_instance(self, tool_name: str) -> BaseTool | None:
        """Return the tool registered under `tool_name`, or None."""
        return AvailableTools.get_tool_instance(tool_name)
