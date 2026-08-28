from typing import ClassVar

from ....domain import BaseTool
from ...config import LoggingConfig
from .current_data_tool import CurrentDateTool

_LAZY_TOOL_KEY = 'readlocalfile'


class AvailableTools:
    """Catalog of the built-in tools an agent can be given by name.

    Tools are registered under lowercase string keys. `ReadLocalFileTool`
    pulls in heavy optional dependencies, so it is loaded on first access and
    marked unavailable when those dependencies are missing.
    """

    __SYSTEM_TOOLS: ClassVar[dict[str, BaseTool]] = {}

    # Lazily loaded tools; a None value means "tried and unavailable".
    __LAZY_SYSTEM_TOOLS: ClassVar[dict[str, BaseTool | None]] = {}

    @classmethod
    def _ensure_system_tools_loaded(cls) -> None:
        """Register the eagerly available system tools once."""
        if not cls.__SYSTEM_TOOLS:
            cls.__SYSTEM_TOOLS['currentdate'] = CurrentDateTool()

    @classmethod
    def get_system_tools(cls) -> dict[str, str]:
        """Return the built-in tools as `{name: description}`.

        Returns:
            A dictionary mapping system tool names to their descriptions.
        """
        return {
            tool_name: tool.description
            for tool_name, tool in cls.__all_instances().items()
        }

    @classmethod
    def get_tool_instance(cls, tool_name: str) -> BaseTool | None:
        """Get a specific tool instance by name.

        Args:
            tool_name: The name of the tool to retrieve (case-insensitive).

        Returns:
            The BaseTool instance if found, None otherwise.
        """
        return cls.__all_instances().get(tool_name.lower())

    @classmethod
    def get_all_tool_instances(cls) -> dict[str, BaseTool]:
        """Get every available tool instance, keyed by registered name.

        Returns:
            A dict of all available tool instances.
        """
        return cls.__all_instances()

    @classmethod
    def __all_instances(cls) -> dict[str, BaseTool]:
        """Return the eager and lazily loaded tools merged into one dict."""
        cls._ensure_system_tools_loaded()
        cls.__try_load_read_local_file_tool()

        instances = cls.__SYSTEM_TOOLS.copy()
        instances.update(
            {k: v for k, v in cls.__LAZY_SYSTEM_TOOLS.items() if v is not None}
        )
        return instances

    @classmethod
    def __try_load_read_local_file_tool(cls) -> None:
        """Load `ReadLocalFileTool`, tolerating missing optional extras.

        Runs at most once: the outcome, including failure, is cached in
        `__LAZY_SYSTEM_TOOLS`.
        """
        if _LAZY_TOOL_KEY in cls.__LAZY_SYSTEM_TOOLS:
            return

        logger = LoggingConfig.get_logger(__name__)
        cls.__LAZY_SYSTEM_TOOLS[_LAZY_TOOL_KEY] = None

        try:
            from .read_local_file_tool import ReadLocalFileTool
        except ImportError as e:
            logger.warning(
                'ReadLocalFileTool not available - optional dependencies '
                'missing. Install with: pip install createagents[file-tools]. '
                'Error: %s',
                e,
            )
            return

        try:
            cls.__LAZY_SYSTEM_TOOLS[_LAZY_TOOL_KEY] = ReadLocalFileTool()
        except RuntimeError as e:
            logger.warning('ReadLocalFileTool not available: %s', e)
        except Exception:
            # A broken optional tool must not take down the whole catalog;
            # it simply stays marked as unavailable.
            logger.exception('Failed to load ReadLocalFileTool')
        else:
            logger.debug('ReadLocalFileTool loaded successfully')
