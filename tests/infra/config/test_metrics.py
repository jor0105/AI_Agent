from datetime import datetime

import pytest

from src.infra.config.metrics import ChatMetrics, MetricsCollector


@pytest.mark.unit
class TestChatMetrics:
    """Testes para ChatMetrics."""

    def test_create_metrics_with_required_fields(self):
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=150.5)

        assert metrics.model == "gpt-5-nano"
        assert metrics.latency_ms == 150.5
        assert metrics.success is True
        assert metrics.tokens_used is None

    def test_create_metrics_with_all_fields(self):
        metrics = ChatMetrics(
            model="gpt-5-nano",
            latency_ms=200.0,
            tokens_used=500,
            prompt_tokens=100,
            completion_tokens=400,
            success=True,
            error_message=None,
        )

        assert metrics.tokens_used == 500
        assert metrics.prompt_tokens == 100
        assert metrics.completion_tokens == 400

    def test_metrics_with_error(self):
        metrics = ChatMetrics(
            model="gpt-5-nano",
            latency_ms=50.0,
            success=False,
            error_message="Connection timeout",
        )

        assert metrics.success is False
        assert metrics.error_message == "Connection timeout"

    def test_to_dict_conversion(self):
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=150.5, tokens_used=100)

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result["model"] == "gpt-5-nano"
        assert result["latency_ms"] == 150.5
        assert result["tokens_used"] == 100
        assert result["success"] is True

    def test_str_representation_success(self):
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=150.5, tokens_used=100)

        string = str(metrics)
        assert "✓" in string
        assert "gpt-5-nano" in string
        assert "150.50ms" in string
        assert "tokens=100" in string

    def test_str_representation_failure(self):
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=50.0, success=False)

        string = str(metrics)
        assert "✗" in string

    def test_timestamp_is_auto_generated(self):
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        assert isinstance(metrics.timestamp, datetime)


@pytest.mark.unit
class TestMetricsCollector:
    """Testes para MetricsCollector."""

    def test_create_collector(self):
        collector = MetricsCollector()
        assert collector.get_all() == []

    def test_add_metrics(self):
        collector = MetricsCollector()
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=100.0)

        collector.add(metrics)

        assert len(collector.get_all()) == 1
        assert collector.get_all()[0] == metrics

    def test_add_multiple_metrics(self):
        collector = MetricsCollector()

        for i in range(5):
            metrics = ChatMetrics(model=f"model-{i}", latency_ms=100.0 * i)
            collector.add(metrics)

        assert len(collector.get_all()) == 5

    def test_get_all_returns_copy(self):
        collector = MetricsCollector()
        metrics = ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        collector.add(metrics)

        list1 = collector.get_all()
        list2 = collector.get_all()

        assert list1 is not list2
        assert list1 == list2

    def test_summary_empty_collector(self):
        collector = MetricsCollector()
        summary = collector.get_summary()

        assert summary["total_requests"] == 0

    def test_summary_with_successful_metrics(self):
        collector = MetricsCollector()

        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50))
        collector.add(
            ChatMetrics(model="gpt-5-nano", latency_ms=200.0, tokens_used=100)
        )
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=150.0, tokens_used=75))

        summary = collector.get_summary()

        assert summary["total_requests"] == 3
        assert summary["successful"] == 3
        assert summary["failed"] == 0
        assert summary["success_rate"] == 100.0
        assert summary["avg_latency_ms"] == 150.0
        assert summary["min_latency_ms"] == 100.0
        assert summary["max_latency_ms"] == 200.0
        assert summary["total_tokens"] == 225

    def test_summary_with_failed_metrics(self):
        collector = MetricsCollector()

        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0, success=True))
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=50.0, success=False))

        summary = collector.get_summary()

        assert summary["total_requests"] == 2
        assert summary["successful"] == 1
        assert summary["failed"] == 1
        assert summary["success_rate"] == 50.0

    def test_clear_collector(self):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0))
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=200.0))

        assert len(collector.get_all()) == 2

        collector.clear()

        assert len(collector.get_all()) == 0

    def test_export_json_returns_string(self):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0))

        json_str = collector.export_json()

        assert isinstance(json_str, str)
        assert "summary" in json_str
        assert "metrics" in json_str
        assert "gpt-5-nano" in json_str

    def test_export_json_to_file(self, tmp_path):
        import json

        collector = MetricsCollector()
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50))

        filepath = tmp_path / "metrics.json"
        collector.export_json(str(filepath))

        assert filepath.exists()

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "summary" in data
        assert "metrics" in data
        assert data["summary"]["total_requests"] == 1

    def test_export_prometheus_format(self):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50))
        collector.add(ChatMetrics(model="phi4-mini:latest", latency_ms=200.0))

        prom_text = collector.export_prometheus()

        assert isinstance(prom_text, str)
        assert "# HELP" in prom_text
        assert "# TYPE" in prom_text
        assert "chat_requests_total" in prom_text
        assert "chat_latency_ms_avg" in prom_text
        assert 'model="gpt-5-nano"' in prom_text

    def test_export_prometheus_to_file(self, tmp_path):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model="gpt-5-nano", latency_ms=100.0))

        filepath = tmp_path / "metrics.prom"
        collector.export_prometheus_to_file(str(filepath))

        assert filepath.exists()

        with open(filepath, "r") as f:
            content = f.read()

        assert "chat_requests_total" in content

    def test_export_prometheus_empty_collector(self):
        collector = MetricsCollector()

        prom_text = collector.export_prometheus()

        assert "No metrics available" in prom_text
