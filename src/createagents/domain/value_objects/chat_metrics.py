from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatMetrics:
    """Represents the metrics for a single chat interaction.

    Attributes:
        model: The name of the model used.
        latency_ms: The request latency in milliseconds.
        tokens_used: The total number of tokens used, if available.
        prompt_tokens: The number of prompt tokens, if available.
        completion_tokens: The number of response tokens, if available.
        timestamp: The timestamp of the request.
        success: A boolean indicating whether the request was successful.
        error_message: An error message, if any.
    """

    model: str
    latency_ms: float
    tokens_used: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    load_duration_ms: float | None = None
    prompt_eval_duration_ms: float | None = None
    eval_duration_ms: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Rounds float metrics to 2 decimal places."""
        if self.latency_ms is not None:
            self.latency_ms = round(self.latency_ms, 2)
        if self.load_duration_ms is not None:
            self.load_duration_ms = round(self.load_duration_ms, 2)
        if self.prompt_eval_duration_ms is not None:
            self.prompt_eval_duration_ms = round(
                self.prompt_eval_duration_ms, 2
            )
        if self.eval_duration_ms is not None:
            self.eval_duration_ms = round(self.eval_duration_ms, 2)

    def to_dict(self) -> dict[str, str | float | int | bool | None]:
        """Converts the metrics to a dictionary."""
        return {
            'model': self.model,
            'latency_ms': self.latency_ms,
            'tokens_used': self.tokens_used,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'load_duration_ms': self.load_duration_ms,
            'prompt_eval_duration_ms': self.prompt_eval_duration_ms,
            'eval_duration_ms': self.eval_duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error_message': self.error_message,
        }

    def __str__(self) -> str:
        """Returns a string representation of the metrics."""
        tokens_info = (
            f', tokens={self.tokens_used}' if self.tokens_used else ''
        )
        detailed_timing = ''
        if self.load_duration_ms:
            detailed_timing += f', load={self.load_duration_ms:.2f}ms'
        if self.prompt_eval_duration_ms:
            detailed_timing += f', p_eval={self.prompt_eval_duration_ms:.2f}ms'
        if self.eval_duration_ms:
            detailed_timing += f', eval={self.eval_duration_ms:.2f}ms'
        status = '✓' if self.success else '✗'
        return f'[{status}] {self.model}: {self.latency_ms:.2f}ms{tokens_info}{detailed_timing}'
