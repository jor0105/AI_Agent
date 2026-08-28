import logging
import time
from dataclasses import dataclass

from ....domain import ChatMetrics
from ...config import (
    DEFAULT_MAX_TOOL_ITERATIONS,
    EnvironmentConfig,
)


@dataclass
class StreamUsageTotals:
    """Token and duration totals accumulated across streaming iterations.

    A streaming turn can span several provider round-trips when tools are
    called. Tokens accumulate across all of them, while durations reflect
    the last iteration reported by the provider.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    load_duration_ms: float | None = None
    prompt_eval_duration_ms: float | None = None
    eval_duration_ms: float | None = None

    def add_tokens(
        self, prompt: int | None = None, completion: int | None = None
    ) -> None:
        """Accumulate token counts, ignoring values the provider omitted."""
        if prompt:
            self.prompt_tokens += prompt
        if completion:
            self.completion_tokens += completion

    @property
    def total_tokens(self) -> int | None:
        """Total tokens, or None when the provider reported no usage."""
        total = self.prompt_tokens + self.completion_tokens
        return total or None

    def to_metrics(self, model: str, latency_ms: float) -> ChatMetrics:
        """Build the successful `ChatMetrics` record for a streaming turn."""
        return ChatMetrics(
            model=model,
            latency_ms=latency_ms,
            tokens_used=self.total_tokens,
            prompt_tokens=self.prompt_tokens or None,
            completion_tokens=self.completion_tokens or None,
            load_duration_ms=self.load_duration_ms,
            prompt_eval_duration_ms=self.prompt_eval_duration_ms,
            eval_duration_ms=self.eval_duration_ms,
            success=True,
        )


class BaseStreamHandler:
    """Shared scaffolding for provider-specific streaming handlers.

    Owns everything that does not depend on a provider's wire format: the
    tool-iteration budget, metric accumulation and the success/error metric
    records. Subclasses implement only the streaming protocol itself.
    """

    def __init__(
        self,
        logger: logging.Logger,
        max_iterations_env_var: str,
        metrics_list: list[ChatMetrics] | None = None,
    ) -> None:
        """Initialize the shared streaming scaffolding.

        Args:
            logger: Logger owned by the concrete handler, so log records keep
                the subclass module name.
            max_iterations_env_var: Environment variable holding this
                provider's tool-iteration budget.
            metrics_list: Optional shared list to append metrics to.
        """
        self._logger = logger
        self._metrics = metrics_list if metrics_list is not None else []
        self._max_tool_iterations = EnvironmentConfig.get_int_env(
            max_iterations_env_var, DEFAULT_MAX_TOOL_ITERATIONS
        )

    @property
    def max_tool_iterations(self) -> int:
        """Maximum number of tool-calling iterations for this provider."""
        return self._max_tool_iterations

    def warn_if_iterations_exhausted(self, iteration: int) -> None:
        """Warn when a streaming turn used up its whole iteration budget."""
        if iteration >= self._max_tool_iterations:
            self._logger.warning(
                'Max tool iterations (%s) reached during streaming',
                self._max_tool_iterations,
            )

    def record_stream_success(
        self,
        model: str,
        start_time: float,
        totals: StreamUsageTotals,
        iteration: int,
    ) -> ChatMetrics:
        """Record metrics for a streaming turn that completed successfully."""
        metrics = totals.to_metrics(
            model, latency_ms=(time.time() - start_time) * 1000
        )
        self._metrics.append(metrics)
        self._logger.info(
            'Streaming chat completed: %s (accumulated over %s iteration(s))',
            metrics,
            iteration,
        )
        return metrics

    def record_stream_error(
        self, model: str, start_time: float, error: Exception
    ) -> ChatMetrics:
        """Record metrics for a streaming turn that failed."""
        metrics = ChatMetrics(
            model=model,
            latency_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(error),
        )
        self._metrics.append(metrics)
        self._logger.error(
            'Error during streaming',
            exc_info=(type(error), error, error.__traceback__),
        )
        return metrics

    def get_metrics(self) -> list[ChatMetrics]:
        """Return a copy of the collected metrics."""
        return self._metrics.copy()
