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
        usage = self._extract_usage(response_api)

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
