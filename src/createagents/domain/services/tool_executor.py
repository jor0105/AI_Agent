import asyncio
import atexit
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from ..interfaces import LoggerInterface
from ..value_objects import BaseTool

_TOOL_THREAD_POOL = ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix='tool-exec',
)
_SYNC_TOOL_POLL_INTERVAL = 0.001
atexit.register(
    _TOOL_THREAD_POOL.shutdown,
    wait=False,
    cancel_futures=True,
)


async def _wait_for_sync_result(future: Future[Any]) -> Any:
    """Wait for a synchronous tool without binding it to an event loop."""
    try:
        while not future.done():
            await asyncio.sleep(_SYNC_TOOL_POLL_INTERVAL)
        return future.result()
    except asyncio.CancelledError:
        future.cancel()
        raise


@dataclass
class ToolExecutionResult:
    """Represents the result of a tool execution.

    Attributes:
        tool_name: Name of the tool that was executed.
        success: Whether the execution was successful.
        result: The result returned by the tool (if successful).
        error: Error message (if execution failed).
        execution_time_ms: Time taken to execute the tool in milliseconds.
    """

    tool_name: str
    success: bool
    result: Any | None = None
    error: str | None = None
    execution_time_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the result.
        """
        return {
            'tool_name': self.tool_name,
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
        }

    def to_llm_message(self) -> str:
        """Format the result as a message for the LLM.

        Returns:
            A formatted string describing the tool execution result.
        """
        if self.success:
            return f"Tool '{self.tool_name}' executed successfully:\n{self.result}"
        return f"Tool '{self.tool_name}' failed with error: {self.error}"


class ToolExecutor:
    """Domain service for executing tools.

    This service follows the Dependency Inversion Principle by depending
    on the abstract BaseTool interface rather than concrete implementations.

    Responsibilities:
    - Execute tools by name with given arguments
    - Handle errors gracefully
    - Return structured results

    Example:
        ```python
        executor = ToolExecutor(available_tools)
        result = executor.execute_tool("web_search", query="Python tutorials")
        if result.success:
            print(result.result)
        ```
    """

    def __init__(self, tools: list[BaseTool], logger: LoggerInterface) -> None:
        """Initialize the executor with available tools and logger.

        Args:
            tools: List of tool instances available for execution.
                   If None, no tools will be available.
            logger: Logger instance for logging tool execution events.
        """
        self._tools_map: dict[str, BaseTool] = {}
        self.__logger = logger

        for tool in tools:
            self._tools_map[tool.name] = tool

        self.__logger.info(
            'ToolExecutor initialized with %s tool(s): %s',
            len(self._tools_map),
            list(self._tools_map.keys()),
        )
        self.__logger.debug(
            'Tool details: %s',
            [
                {'name': t.name, 'description': t.description[:50]}
                for t in tools
            ],
        )

    def get_available_tool_names(self) -> list[str]:
        """Get list of available tool names.

        Returns:
            List of tool names that can be executed.
        """
        return list(self._tools_map.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            True if the tool exists, False otherwise.
        """
        return tool_name in self._tools_map

    async def execute_tool(
        self, tool_name: str, **kwargs: Any
    ) -> ToolExecutionResult:
        """Execute a tool by name with given arguments.

        This method provides safe execution with comprehensive error handling,
        ensuring that tool failures don't crash the agent.

        Args:
            tool_name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool's execute method.

        Returns:
            A ToolExecutionResult containing the execution outcome.

        Example:
            ```python
            result = await executor.execute_tool(
                "web_search",
                query="What is Clean Architecture?"
            )
            ```
        """
        start_time = time.time()

        self.__logger.info("Attempting to execute tool: '%s'", tool_name)
        self.__logger.debug('Tool arguments: %s', kwargs)

        if not self.has_tool(tool_name):
            available = ', '.join(self.get_available_tool_names())
            error_msg = (
                f"Tool '{tool_name}' not found. "
                f'Available tools: {available if available else "None"}'
            )
            self.__logger.error(error_msg)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        try:
            tool = self._tools_map[tool_name]
            self.__logger.debug(
                "Executing tool '%s' with %s argument(s)",
                tool_name,
                len(kwargs),
            )

            if asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**kwargs)
            else:
                future = _TOOL_THREAD_POOL.submit(
                    tool.execute,
                    **kwargs,
                )
                result = await _wait_for_sync_result(future)

            execution_time = (time.time() - start_time) * 1000

            self.__logger.info(
                "Tool '%s' executed successfully in %.2fms",
                tool_name,
                execution_time,
            )
            self.__logger.debug(
                'Tool result (first 200 chars): %s...', str(result)[:200]
            )

            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except TypeError as e:
            return self.__failure(
                tool_name,
                start_time,
                f"Invalid arguments for tool '{tool_name}': {e!s}",
            )

        except (ValueError, RuntimeError) as e:
            return self.__failure(
                tool_name,
                start_time,
                f"Error executing tool '{tool_name}': {e!s}",
            )

        # A bug in third-party tool code must degrade to a failed result, not
        # crash the agent mid-conversation. `__failure` logs the traceback.
        except Exception as e:  # noqa: BLE001
            return self.__failure(
                tool_name,
                start_time,
                f"Internal error in tool '{tool_name}': "
                f'{type(e).__name__}: {e!s}',
            )

    def __failure(
        self, tool_name: str, start_time: float, error_msg: str
    ) -> ToolExecutionResult:
        """Log a failed execution and build its result.

        Must be called from inside an `except` block: the active exception is
        what gives the log record its traceback.

        Args:
            tool_name: Name of the tool that failed.
            start_time: When the execution attempt started.
            error_msg: The caller-facing description of the failure.

        Returns:
            The failed `ToolExecutionResult`, timed from `start_time`.
        """
        execution_time = (time.time() - start_time) * 1000
        # Called from the caller's `except` block, so the active exception is
        # still set and the traceback is captured.
        self.__logger.exception(  # noqa: LOG004
            "Error executing tool '%s': %s (execution time: %.2fms)",
            tool_name,
            error_msg,
            execution_time,
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            success=False,
            error=error_msg,
            execution_time_ms=execution_time,
        )
