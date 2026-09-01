import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, override

from ....domain import ChatMetrics
from ...config import LoggingConfig
from .durations import nanoseconds_to_milliseconds


@dataclass(frozen=True)
class ProviderUsage:
    """What a provider reported about one completed (non-streamed) call."""

    tokens_used: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    load_duration_ms: float | None = None
    prompt_eval_duration_ms: float | None = None
    eval_duration_ms: float | None = None

    def add(self, other: 'ProviderUsage') -> 'ProviderUsage':
        """Add usage from another provider call to this usage record."""
        prompt_tokens = _add_optional(self.prompt_tokens, other.prompt_tokens)
        completion_tokens = _add_optional(
            self.completion_tokens, other.completion_tokens
        )
        tokens_used = _add_optional(
            self._total_tokens(), other._total_tokens()
        )

        return ProviderUsage(
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            load_duration_ms=_add_optional(
                self.load_duration_ms, other.load_duration_ms
            ),
            prompt_eval_duration_ms=_add_optional(
                self.prompt_eval_duration_ms, other.prompt_eval_duration_ms
            ),
            eval_duration_ms=_add_optional(
                self.eval_duration_ms, other.eval_duration_ms
            ),
        )

    def _total_tokens(self) -> int | None:
        """Return the reported total or derive it from both token counters."""
        if self.tokens_used is not None:
            return self.tokens_used
        if (
            self.prompt_tokens is not None
            and self.completion_tokens is not None
        ):
            return self.prompt_tokens + self.completion_tokens
        return None


def _add_optional[NumericT: (int, float)](
    first: NumericT | None, second: NumericT | None
) -> NumericT | None:
    """Add optional numeric values while preserving an absent measurement."""
    if first is None:
        return second
    if second is None:
        return first
    return first + second


class MetricsRecorder(ABC):
    """Turns a provider response into `ChatMetrics` and stores it.

    Reading usage out of a response is the only provider-specific part, so
    subclasses implement just that; everything else is shared.
    """

    def __init__(self, metrics_list: list[ChatMetrics] | None = None) -> None:
        """Initialize the metrics recorder.

        Args:
            metrics_list: Optional shared list to append metrics to. A new
                list is created when omitted.

        """
        self._metrics = metrics_list if metrics_list is not None else []
        self._logger = LoggingConfig.get_logger(__name__)

    @abstractmethod
    def _extract_usage(self, response_api: Any) -> ProviderUsage:
        """Read token counts and durations out of a provider response."""

    def record_success_metrics(
        self, model: str, start_time: float, response_api: Any
    ) -> None:
        """Record metrics for a successful operation.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            response_api: The response object from the API.

        """
        self.__record_success_metrics(
            model, start_time, self._extract_usage(response_api)
        )

    def record_success_metrics_from_responses(
        self, model: str, start_time: float, responses: list[Any]
    ) -> None:
        """Record one metric after several provider calls form one turn.

        Tool calling can require multiple Responses API requests before the
        assistant returns its final answer. Each response reports usage for
        that request, so the metric for the logical turn must aggregate them.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            responses: Responses returned during the logical turn.

        """
        usage = ProviderUsage()
        for response in responses:
            usage = usage.add(self._extract_usage(response))
        self.__record_success_metrics(model, start_time, usage)

    def __record_success_metrics(
        self, model: str, start_time: float, usage: ProviderUsage
    ) -> None:
        """Append a successful metric built from normalized provider usage."""
        metrics = ChatMetrics(
            model=model,
            latency_ms=(time.time() - start_time) * 1000,
            tokens_used=usage.tokens_used,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            load_duration_ms=usage.load_duration_ms,
            prompt_eval_duration_ms=usage.prompt_eval_duration_ms,
            eval_duration_ms=usage.eval_duration_ms,
            success=True,
        )
        self._metrics.append(metrics)
        self._logger.info('Chat completed: %s', metrics)

    def record_error_metrics(
        self, model: str, start_time: float, error: Any
    ) -> None:
        """Record metrics for a failed operation.

        Args:
            model: The model name used for the operation.
            start_time: The timestamp when the operation started.
            error: The error that occurred (string or Exception).

        """
        metrics = ChatMetrics(
            model=model,
            latency_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(error) if error else 'Unknown error',
        )
        self._metrics.append(metrics)

    def get_metrics(self) -> list[ChatMetrics]:
        """Return a copy of collected metrics.

        Returns:
            A copy of the metrics list.

        """
        return self._metrics.copy()


class OpenAIMetricsRecorder(MetricsRecorder):
    """Reads usage from an OpenAI Responses API object."""

    @override
    def _extract_usage(self, response_api: Any) -> ProviderUsage:
        """Read the `usage` attribute; OpenAI reports no durations."""
        usage = getattr(response_api, 'usage', None)
        if usage is None:
            return ProviderUsage()

        total_tokens = getattr(usage, 'total_tokens', None)
        prompt_tokens = getattr(usage, 'input_tokens', None)
        if prompt_tokens is None:
            prompt_tokens = getattr(usage, 'prompt_tokens', None)

        completion_tokens = getattr(usage, 'output_tokens', None)
        if completion_tokens is None:
            completion_tokens = getattr(usage, 'completion_tokens', None)

        if (
            total_tokens is None
            and prompt_tokens is not None
            and completion_tokens is not None
        ):
            total_tokens = prompt_tokens + completion_tokens

        return ProviderUsage(
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


class OllamaMetricsRecorder(MetricsRecorder):
    """Reads usage from an Ollama chat response."""

    @override
    def _extract_usage(self, response_api: Any) -> ProviderUsage:
        """Read Ollama's counts and convert its nanosecond durations."""
        prompt_tokens = response_api.get('prompt_eval_count', 0)
        completion_tokens = response_api.get('eval_count', 0)

        return ProviderUsage(
            tokens_used=prompt_tokens + completion_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            load_duration_ms=nanoseconds_to_milliseconds(
                response_api.get('load_duration')
            ),
            prompt_eval_duration_ms=nanoseconds_to_milliseconds(
                response_api.get('prompt_eval_duration')
            ),
            eval_duration_ms=nanoseconds_to_milliseconds(
                response_api.get('eval_duration')
            ),
        )
