import concurrent.futures
import threading
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

    def test_collector_with_custom_max_metrics(self):
        """Testa criação de collector com limite customizado."""
        collector = MetricsCollector(max_metrics=100)

        assert collector._max_metrics == 100

    def test_collector_uses_default_max_metrics(self):
        """Testa que usa MAX_METRICS por padrão."""
        collector = MetricsCollector()

        assert collector._max_metrics == MetricsCollector.MAX_METRICS
        assert collector._max_metrics == 10000

    def test_max_metrics_limit_enforced(self):
        """Testa que o limite máximo de métricas é respeitado."""
        collector = MetricsCollector(max_metrics=10)

        # Adiciona 15 métricas
        for i in range(15):
            collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))

        # Deve manter apenas as últimas 10
        metrics = collector.get_all()
        assert len(metrics) == 10

        # Verifica que são as mais recentes
        models = [m.model for m in metrics]
        assert "model-5" in models
        assert "model-14" in models
        assert "model-0" not in models
        assert "model-4" not in models

    def test_max_metrics_removes_oldest_first(self):
        """Testa que as métricas mais antigas são removidas primeiro."""
        collector = MetricsCollector(max_metrics=3)

        m1 = ChatMetrics(model="first", latency_ms=100.0)
        m2 = ChatMetrics(model="second", latency_ms=200.0)
        m3 = ChatMetrics(model="third", latency_ms=300.0)
        m4 = ChatMetrics(model="fourth", latency_ms=400.0)

        collector.add(m1)
        collector.add(m2)
        collector.add(m3)

        metrics = collector.get_all()
        assert len(metrics) == 3
        assert metrics[0].model == "first"

        # Adiciona quarta, deve remover primeira
        collector.add(m4)

        metrics = collector.get_all()
        assert len(metrics) == 3
        assert metrics[0].model == "second"
        assert metrics[2].model == "fourth"

    def test_thread_safety_add_metrics(self):
        """Testa que add() é thread-safe."""
        collector = MetricsCollector()
        errors = []

        def add_metric(i):
            try:
                collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_metric, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 100

    def test_thread_safety_get_all(self):
        """Testa que get_all() é thread-safe."""
        collector = MetricsCollector()

        # Adiciona métricas
        for i in range(10):
            collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))

        results = []
        errors = []
        lock = threading.Lock()

        def get_metrics():
            try:
                metrics = collector.get_all()
                with lock:
                    results.append(len(metrics))
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_metrics) for _ in range(50)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert all(r == 10 for r in results)

    def test_thread_safety_get_summary(self):
        """Testa que get_summary() é thread-safe."""
        collector = MetricsCollector()

        for i in range(5):
            collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0 + i * 10))

        results = []
        errors = []
        lock = threading.Lock()

        def get_summary():
            try:
                summary = collector.get_summary()
                with lock:
                    results.append(summary["total_requests"])
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(get_summary) for _ in range(30)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert all(r == 5 for r in results)

    def test_thread_safety_clear(self):
        """Testa que clear() é thread-safe."""
        collector = MetricsCollector()

        for i in range(10):
            collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))

        errors = []

        def clear_metrics():
            try:
                collector.clear()
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(clear_metrics) for _ in range(10)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 0

    def test_concurrent_add_and_read(self):
        """Testa operações concorrentes de adicionar e ler."""
        collector = MetricsCollector()
        errors = []
        read_results = []
        lock = threading.Lock()

        def add_metric(i):
            try:
                collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))
            except Exception as e:
                with lock:
                    errors.append(("add", str(e)))

        def read_metrics():
            try:
                metrics = collector.get_all()
                with lock:
                    read_results.append(len(metrics))
            except Exception as e:
                with lock:
                    errors.append(("read", str(e)))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            add_futures = [executor.submit(add_metric, i) for i in range(50)]
            read_futures = [executor.submit(read_metrics) for _ in range(20)]

            all_futures = add_futures + read_futures
            concurrent.futures.wait(all_futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 50

    def test_concurrent_add_with_limit(self):
        """Testa adições concorrentes respeitando limite."""
        collector = MetricsCollector(max_metrics=50)
        errors = []

        def add_metric(i):
            try:
                collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(add_metric, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        # Deve manter apenas 50
        assert len(collector.get_all()) == 50

    def test_summary_respects_limit(self):
        """Testa que summary funciona corretamente após atingir limite."""
        collector = MetricsCollector(max_metrics=5)

        for i in range(10):
            success = i % 2 == 0
            collector.add(
                ChatMetrics(
                    model=f"model-{i}", latency_ms=100.0 + i * 10, success=success
                )
            )

        summary = collector.get_summary()

        # Deve ter apenas as últimas 5
        assert summary["total_requests"] == 5
        assert summary["avg_latency_ms"] >= 150.0  # Métricas mais recentes

    def test_clear_resets_to_empty(self):
        """Testa que clear reseta completamente."""
        collector = MetricsCollector(max_metrics=10)

        for i in range(15):
            collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))

        assert len(collector.get_all()) == 10

        collector.clear()

        assert len(collector.get_all()) == 0
        summary = collector.get_summary()
        assert summary["total_requests"] == 0

    def test_metrics_with_none_tokens_in_summary(self):
        """Testa summary com métricas sem tokens."""
        collector = MetricsCollector()

        collector.add(ChatMetrics(model="model1", latency_ms=100.0, tokens_used=None))
        collector.add(ChatMetrics(model="model2", latency_ms=200.0, tokens_used=50))
        collector.add(ChatMetrics(model="model3", latency_ms=300.0, tokens_used=None))

        summary = collector.get_summary()

        assert summary["total_requests"] == 3
        assert summary["total_tokens"] == 50  # Apenas o que tem token

    def test_massive_concurrent_stress_test(self):
        """Teste de stress com muitas threads."""
        collector = MetricsCollector(max_metrics=1000)
        errors = []

        def random_operation(i):
            try:
                if i % 3 == 0:
                    collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))
                elif i % 3 == 1:
                    collector.get_all()
                else:
                    collector.get_summary()
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(random_operation, i) for i in range(500)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        # Deve ter no máximo 1000 métricas
        assert len(collector.get_all()) <= 1000

    def test_lock_prevents_race_conditions(self):
        """Testa que lock previne race conditions."""
        collector = MetricsCollector(max_metrics=10)
        counters = {"add": 0, "get": 0}
        lock = threading.Lock()

        def add_and_count(i):
            collector.add(ChatMetrics(model=f"model-{i}", latency_ms=100.0))
            with lock:
                counters["add"] += 1

        def get_and_count():
            _ = collector.get_all()
            with lock:
                counters["get"] += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            add_futures = [executor.submit(add_and_count, i) for i in range(50)]
            get_futures = [executor.submit(get_and_count) for _ in range(50)]

            all_futures = add_futures + get_futures
            concurrent.futures.wait(all_futures)

        # Todas as operações devem ter sido contadas
        assert counters["add"] == 50
        assert counters["get"] == 50
        # Collector deve ter no máximo 10
        assert len(collector.get_all()) == 10
