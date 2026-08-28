"""Tool wiring shared by every provider handler.

Each provider has two entry points -- buffered and streaming -- that need the
same two things before a turn starts: the tool schemas in the provider's wire
format, and an executor able to run those tools. Only the formatter differs,
so the preparation is written once here.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ....domain import BaseTool, ToolExecutor
from ...config import create_logger

#: Converts domain tools into one provider's tool-schema payload.
type SchemaFormatter = Callable[[list[BaseTool]], list[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSession:
    """The tool schemas and executor a single chat turn runs with.

    Both fields are None when the agent declares no tools, which is the
    signal the handlers use to skip the tool-calling branch entirely.
    """

    executor: ToolExecutor | None = None
    schemas: list[dict[str, Any]] | None = None

    @classmethod
    def prepare(
        cls,
        tools: list[BaseTool] | None,
        formatter: SchemaFormatter,
        logger: logging.Logger,
        executor_logger_name: str,
    ) -> 'ToolSession':
        """Build the session for a turn, or an empty one when tools are absent.

        Args:
            tools: The agent's tools, or None when it declares none.
            formatter: Converts the tools to the provider's schema format.
            logger: Logger of the calling handler, used for the debug trace.
            executor_logger_name: Logger name given to the `ToolExecutor`, so
                its records stay attributable to the calling handler.

        Returns:
            A populated session, or an empty one when `tools` is falsy.
        """
        if not tools:
            return cls()

        logger.debug('Tools enabled: %s', [tool.name for tool in tools])
        return cls(
            executor=ToolExecutor(tools, create_logger(executor_logger_name)),
            schemas=formatter(tools),
        )
