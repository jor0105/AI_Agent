import json
import threading

from ...domain import ChatMetrics


class MetricsCollector:
    """A thread-safe collector for aggregated metrics analysis.

    It has a storage limit to prevent memory leaks.
    """

    MAX_METRICS = 10000

    def __init__(self, max_metrics: int = MAX_METRICS) -> None:
        """Initializes the metrics collector.

        Args:
            max_metrics: The maximum number of metrics to store (default: 10,000).
        """
        self._metrics: list[ChatMetrics] = []
        self._lock = threading.Lock()
        self._max_metrics = max_metrics

    def add(self, metrics: ChatMetrics) -> None:
        """Adds metrics to the collection in a thread-safe manner.

        If the collection exceeds the maximum size, the oldest metrics are removed.
        """
        with self._lock:
            self._metrics.append(metrics)
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics :]

    def get_all(self) -> list[ChatMetrics]:
        """Returns a thread-safe copy of all collected metrics."""
        with self._lock:
            return self._metrics.copy()

    def get_summary(self) -> dict[str, int | float]:
        """Returns a statistical summary of the metrics in a thread-safe manner.

        Returns:
            A dictionary containing aggregated statistics.
        """
        with self._lock:
            if not self._metrics:
                return {'total_requests': 0}

            total_requests = len(self._metrics)
            successful = sum(1 for m in self._metrics if m.success)
            failed = total_requests - successful

            latencies = [m.latency_ms for m in self._metrics]
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)

            total_tokens = sum(
                m.tokens_used
                for m in self._metrics
                if m.tokens_used is not None
            )

            return {
                'total_requests': total_requests,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_requests) * 100,
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'total_tokens': total_tokens,
            }

    def clear(self) -> None:
        """Clears all metrics in a thread-safe manner."""
        with self._lock:
            self._metrics.clear()

    def export_json(self, filepath: str | None = None) -> str:
        """Exports the metrics in JSON format.

        Args:
            filepath: An optional file path to save the JSON data.
                      If not provided, the method returns the JSON string.

        Returns:
            A JSON string containing all metrics.
        """
        data = {
            'summary': self.get_summary(),
            'metrics': [m.to_dict() for m in self._metrics],
        }

        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def export_prometheus(self) -> str:
        """Exports metrics in a Prometheus-compatible format.

        This method generates metrics in the Prometheus text format, including:
        - `chat_requests_total`: Total number of requests.
        - `chat_requests_success_total`: Total number of successful requests.
        - `chat_requests_failed_total`: Total number of failed requests.
        - `chat_latency_ms`: A histogram of latencies.
        - `chat_tokens_total`: The total number of tokens used.

        Returns:
            A string with the metrics in Prometheus format.
        """
        if not self._metrics:
            return '# No metrics available\n'

        summary = self.get_summary()

        lines = []

        lines.append(
            '# HELP chat_requests_total Total number of chat requests'
        )
        lines.append('# TYPE chat_requests_total counter')
        lines.append(f'chat_requests_total {summary["total_requests"]}')
        lines.append('')

        lines.append(
            '# HELP chat_requests_success_total Total number of successful chat requests'
        )
        lines.append('# TYPE chat_requests_success_total counter')
        lines.append(f'chat_requests_success_total {summary["successful"]}')
        lines.append('')

        lines.append(
            '# HELP chat_requests_failed_total Total number of failed chat requests'
        )
        lines.append('# TYPE chat_requests_failed_total counter')
        lines.append(f'chat_requests_failed_total {summary["failed"]}')
        lines.append('')

        lines.append(
            '# HELP chat_latency_ms_avg Average latency in milliseconds'
        )
        lines.append('# TYPE chat_latency_ms_avg gauge')
        lines.append(f'chat_latency_ms_avg {summary["avg_latency_ms"]:.2f}')
        lines.append('')

        lines.append(
            '# HELP chat_latency_ms_min Minimum latency in milliseconds'
        )
        lines.append('# TYPE chat_latency_ms_min gauge')
        lines.append(f'chat_latency_ms_min {summary["min_latency_ms"]:.2f}')
        lines.append('')

        lines.append(
            '# HELP chat_latency_ms_max Maximum latency in milliseconds'
        )
        lines.append('# TYPE chat_latency_ms_max gauge')
        lines.append(f'chat_latency_ms_max {summary["max_latency_ms"]:.2f}')
        lines.append('')

        lines.append('# HELP chat_tokens_total Total number of tokens used')
        lines.append('# TYPE chat_tokens_total counter')
        lines.append(f'chat_tokens_total {summary["total_tokens"]}')
        lines.append('')

        lines.append('# HELP chat_requests_by_model Total requests by model')
        lines.append('# TYPE chat_requests_by_model counter')

        model_counts: dict[str, int] = {}
        for m in self._metrics:
            model_counts[m.model] = model_counts.get(m.model, 0) + 1

        for model, count in model_counts.items():
            lines.append(f'chat_requests_by_model{{model="{model}"}} {count}')

        return '\n'.join(lines)

    def export_prometheus_to_file(self, filepath: str) -> None:
        """Exports metrics to a file in Prometheus format.

        Args:
            filepath: The file path to save the metrics.
        """
        content = self.export_prometheus()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
