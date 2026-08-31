import concurrent.futures
import threading
from datetime import datetime

import pytest

from createagents.domain import ChatMetrics
from createagents.infra import MetricsCollector
from tests.test_constants import OLLAMA_MODEL_PHI, OPENAI_MODEL_NANO


@pytest.mark.unit
class TestChatMetrics:
    def test_create_metrics_with_required_fields(self):
        metrics = ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=150.5)

        assert metrics.model == OPENAI_MODEL_NANO
        assert metrics.latency_ms == 150.5
        assert metrics.success is True
        assert metrics.tokens_used is None

    def test_create_metrics_with_all_fields(self):
        metrics = ChatMetrics(
            model=OPENAI_MODEL_NANO,
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
            model=OPENAI_MODEL_NANO,
            latency_ms=50.0,
            success=False,
            error_message='Connection timeout',
        )

        assert metrics.success is False
        assert metrics.error_message == 'Connection timeout'

    def test_to_dict_conversion(self):
        metrics = ChatMetrics(
            model=OPENAI_MODEL_NANO, latency_ms=150.5, tokens_used=100
        )

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result['model'] == OPENAI_MODEL_NANO
        assert result['latency_ms'] == 150.5
        assert result['tokens_used'] == 100
        assert result['success'] is True

    def test_str_reapplication_success(self):
        metrics = ChatMetrics(
            model=OPENAI_MODEL_NANO, latency_ms=150.5, tokens_used=100
        )

        string = str(metrics)
        assert '✓' in string
        assert OPENAI_MODEL_NANO in string
        assert '150.50ms' in string
        assert 'tokens=100' in string

    def test_str_reapplication_failure(self):
        metrics = ChatMetrics(
            model=OPENAI_MODEL_NANO, latency_ms=50.0, success=False
        )

        string = str(metrics)
        assert '✗' in string

    def test_timestamp_is_auto_generated(self):
        metrics = ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=100.0)
        assert isinstance(metrics.timestamp, datetime)


@pytest.mark.unit
class TestMetricsCollector:
    def test_create_collector(self):
        collector = MetricsCollector()
        assert collector.get_all() == []

    def test_add_metrics(self):
        collector = MetricsCollector()
        metrics = ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=100.0)

        collector.add(metrics)

        assert len(collector.get_all()) == 1
        assert collector.get_all()[0] == metrics

    def test_add_multiple_metrics(self):
        collector = MetricsCollector()

        for i in range(5):
            metrics = ChatMetrics(model=f'model-{i}', latency_ms=100.0 * i)
            collector.add(metrics)

        assert len(collector.get_all()) == 5

    def test_get_all_returns_copy(self):
        collector = MetricsCollector()
        metrics = ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=100.0)
        collector.add(metrics)

        list1 = collector.get_all()
        list2 = collector.get_all()

        assert list1 is not list2
        assert list1 == list2

    def test_summary_empty_collector(self):
        collector = MetricsCollector()
        summary = collector.get_summary()

        assert summary['total_requests'] == 0

    def test_summary_with_successful_metrics(self):
        collector = MetricsCollector()

        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=100.0, tokens_used=50
            )
        )
        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=200.0, tokens_used=100
            )
        )
        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=150.0, tokens_used=75
            )
        )

        summary = collector.get_summary()

        assert summary['total_requests'] == 3
        assert summary['successful'] == 3
        assert summary['failed'] == 0
        assert summary['success_rate'] == 100.0
        assert summary['avg_latency_ms'] == 150.0
        assert summary['min_latency_ms'] == 100.0
        assert summary['max_latency_ms'] == 200.0
        assert summary['total_tokens'] == 225

    def test_summary_with_failed_metrics(self):
        collector = MetricsCollector()

        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=100.0, success=True
            )
        )
        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=50.0, success=False
            )
        )

        summary = collector.get_summary()

        assert summary['total_requests'] == 2
        assert summary['successful'] == 1
        assert summary['failed'] == 1
        assert summary['success_rate'] == 50.0

    def test_clear_collector(self):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=100.0))
        collector.add(ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=200.0))

        assert len(collector.get_all()) == 2

        collector.clear()

        assert len(collector.get_all()) == 0

    def test_export_json_returns_string(self):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=100.0))

        json_str = collector.export_json()

        assert isinstance(json_str, str)
        assert 'summary' in json_str
        assert 'metrics' in json_str
        assert OPENAI_MODEL_NANO in json_str

    def test_export_json_to_file(self, tmp_path):
        import json

        collector = MetricsCollector()
        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=100.0, tokens_used=50
            )
        )

        filepath = tmp_path / 'metrics.json'
        collector.export_json(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)

        assert 'summary' in data
        assert 'metrics' in data
        assert data['summary']['total_requests'] == 1

    def test_export_prometheus_format(self):
        collector = MetricsCollector()
        collector.add(
            ChatMetrics(
                model=OPENAI_MODEL_NANO, latency_ms=100.0, tokens_used=50
            )
        )
        collector.add(ChatMetrics(model=OLLAMA_MODEL_PHI, latency_ms=200.0))

        prom_text = collector.export_prometheus()

        assert isinstance(prom_text, str)
        assert '# HELP' in prom_text
        assert '# TYPE' in prom_text
        assert 'chat_requests_total' in prom_text
        assert 'chat_latency_ms_avg' in prom_text
        assert f'model="{OPENAI_MODEL_NANO}"' in prom_text

    def test_export_prometheus_to_file(self, tmp_path):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model=OPENAI_MODEL_NANO, latency_ms=100.0))

        filepath = tmp_path / 'metrics.prom'
        collector.export_prometheus_to_file(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            content = f.read()

        assert 'chat_requests_total' in content

    def test_export_prometheus_empty_collector(self):
        collector = MetricsCollector()

        prom_text = collector.export_prometheus()

        assert 'No metrics available' in prom_text

    def test_collector_with_custom_max_metrics(self):
        collector = MetricsCollector(max_metrics=100)

        assert collector._max_metrics == 100

    def test_collector_uses_default_max_metrics(self):
        collector = MetricsCollector()

        assert collector._max_metrics == MetricsCollector.MAX_METRICS
        assert collector._max_metrics == 10000

    def test_max_metrics_limit_enforced(self):
        collector = MetricsCollector(max_metrics=10)

        for i in range(15):
            collector.add(ChatMetrics(model=f'model-{i}', latency_ms=100.0))

        metrics = collector.get_all()
        assert len(metrics) == 10

        models = [m.model for m in metrics]
        assert 'model-5' in models
        assert 'model-14' in models
        assert 'model-0' not in models
        assert 'model-4' not in models

    def test_max_metrics_removes_oldest_first(self):
        collector = MetricsCollector(max_metrics=3)

        m1 = ChatMetrics(model='first', latency_ms=100.0)
        m2 = ChatMetrics(model='second', latency_ms=200.0)
        m3 = ChatMetrics(model='third', latency_ms=300.0)
        m4 = ChatMetrics(model='fourth', latency_ms=400.0)

        collector.add(m1)
        collector.add(m2)
        collector.add(m3)

        metrics = collector.get_all()
        assert len(metrics) == 3
        assert metrics[0].model == 'first'

        collector.add(m4)

        metrics = collector.get_all()
        assert len(metrics) == 3
        assert metrics[0].model == 'second'
        assert metrics[2].model == 'fourth'

    def test_thread_safety_add_metrics(self):
        collector = MetricsCollector()
        errors = []

        def add_metric(i):
            try:
                collector.add(
                    ChatMetrics(model=f'model-{i}', latency_ms=100.0)
                )
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_metric, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 100

    def test_thread_safety_get_all(self):
        collector = MetricsCollector()

        for i in range(10):
            collector.add(ChatMetrics(model=f'model-{i}', latency_ms=100.0))

        results = []
        errors = []
        lock = threading.Lock()

        def get_metrics():
            try:
                metrics = collector.get_all()
                with lock:
                    results.append(len(metrics))
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_metrics) for _ in range(50)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert all(r == 10 for r in results)

    def test_thread_safety_get_summary(self):
        collector = MetricsCollector()

        for i in range(5):
            collector.add(
                ChatMetrics(model=f'model-{i}', latency_ms=100.0 + i * 10)
            )

        results = []
        errors = []
        lock = threading.Lock()

        def get_summary():
            try:
                summary = collector.get_summary()
                with lock:
                    results.append(summary['total_requests'])
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(get_summary) for _ in range(30)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert all(r == 5 for r in results)

    def test_thread_safety_clear(self):
        collector = MetricsCollector()

        for i in range(10):
            collector.add(ChatMetrics(model=f'model-{i}', latency_ms=100.0))

        errors = []

        def clear_metrics():
            try:
                collector.clear()
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(clear_metrics) for _ in range(10)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 0

    def test_concurrent_add_and_read(self):
        collector = MetricsCollector()
        errors = []
        read_results = []
        lock = threading.Lock()

        def add_metric(i):
            try:
                collector.add(
                    ChatMetrics(model=f'model-{i}', latency_ms=100.0)
                )
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                with lock:
                    errors.append(('add', str(e)))

        def read_metrics():
            try:
                metrics = collector.get_all()
                with lock:
                    read_results.append(len(metrics))
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                with lock:
                    errors.append(('read', str(e)))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            add_futures = [executor.submit(add_metric, i) for i in range(50)]
            read_futures = [executor.submit(read_metrics) for _ in range(20)]

            all_futures = add_futures + read_futures
            concurrent.futures.wait(all_futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 50

    def test_concurrent_add_with_limit(self):
        collector = MetricsCollector(max_metrics=50)
        errors = []

        def add_metric(i):
            try:
                collector.add(
                    ChatMetrics(model=f'model-{i}', latency_ms=100.0)
                )
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(add_metric, i) for i in range(100)]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(collector.get_all()) == 50

    def test_summary_respects_limit(self):
        collector = MetricsCollector(max_metrics=5)

        for i in range(10):
            success = i % 2 == 0
            collector.add(
                ChatMetrics(
                    model=f'model-{i}',
                    latency_ms=100.0 + i * 10,
                    success=success,
                )
            )

        summary = collector.get_summary()

        assert summary['total_requests'] == 5
        assert summary['avg_latency_ms'] >= 150.0

    def test_clear_resets_to_empty(self):
        collector = MetricsCollector(max_metrics=10)

        for i in range(15):
            collector.add(ChatMetrics(model=f'model-{i}', latency_ms=100.0))

        assert len(collector.get_all()) == 10

        collector.clear()

        assert len(collector.get_all()) == 0
        summary = collector.get_summary()
        assert summary['total_requests'] == 0

    def test_metrics_with_none_tokens_in_summary(self):
        collector = MetricsCollector()

        collector.add(
            ChatMetrics(model='model1', latency_ms=100.0, tokens_used=None)
        )
        collector.add(
            ChatMetrics(model='model2', latency_ms=200.0, tokens_used=50)
        )
        collector.add(
            ChatMetrics(model='model3', latency_ms=300.0, tokens_used=None)
        )

        summary = collector.get_summary()

        assert summary['total_requests'] == 3
        assert summary['total_tokens'] == 50

    def test_massive_concurrent_stress_test(self):
        collector = MetricsCollector(max_metrics=1000)
        errors = []

        def random_operation(i):
            try:
                if i % 3 == 0:
                    collector.add(
                        ChatMetrics(model=f'model-{i}', latency_ms=100.0)
                    )
                elif i % 3 == 1:
                    collector.get_all()
                else:
                    collector.get_summary()
            # Capture worker failures for the assertion after all futures finish.
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(random_operation, i) for i in range(500)
            ]
            concurrent.futures.wait(futures)

        assert len(errors) == 0
        assert len(collector.get_all()) <= 1000

    def test_lock_prevents_race_conditions(self):
        collector = MetricsCollector(max_metrics=10)
        counters = {'add': 0, 'get': 0}
        lock = threading.Lock()

        def add_and_count(i):
            collector.add(ChatMetrics(model=f'model-{i}', latency_ms=100.0))
            with lock:
                counters['add'] += 1

        def get_and_count():
            _ = collector.get_all()
            with lock:
                counters['get'] += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            add_futures = [
                executor.submit(add_and_count, i) for i in range(50)
            ]
            get_futures = [executor.submit(get_and_count) for _ in range(50)]

            all_futures = add_futures + get_futures
            concurrent.futures.wait(all_futures)

        assert counters['add'] == 50
        assert counters['get'] == 50
        assert len(collector.get_all()) == 10

    def test_export_json_with_unicode_characters(self):
        collector = MetricsCollector()
        collector.add(
            ChatMetrics(
                model='modelo-português-日本語',
                latency_ms=100.0,
                error_message='Erro: não encontrado 🚫',
            )
        )

        json_str = collector.export_json()

        assert 'português' in json_str
        assert '日本語' in json_str
        assert '🚫' in json_str or 'não encontrado' in json_str

    def test_export_prometheus_with_special_model_names(self):
        collector = MetricsCollector()
        collector.add(ChatMetrics(model='model:v1.0', latency_ms=100.0))
        collector.add(
            ChatMetrics(
                model='model-with-dashes_and_underscores', latency_ms=150.0
            )
        )

        prom_text = collector.export_prometheus()

        assert 'model:v1.0' in prom_text or 'model' in prom_text
        assert (
            'model-with-dashes_and_underscores' in prom_text
            or 'dashes' in prom_text
        )

    def test_metrics_to_dict_with_none_values(self):
        metrics = ChatMetrics(
            model='test-model',
            latency_ms=100.0,
            tokens_used=None,
            prompt_tokens=None,
            completion_tokens=None,
            error_message=None,
        )

        result = metrics.to_dict()

        assert result['tokens_used'] is None
        assert result['prompt_tokens'] is None
        assert result['completion_tokens'] is None
        assert result['error_message'] is None

    def test_collector_export_json_empty_summary(self):
        import json

        collector = MetricsCollector()
        json_str = collector.export_json()

        data = json.loads(json_str)

        assert data['summary']['total_requests'] == 0
        assert data['metrics'] == []

    def test_summary_with_only_failed_requests(self):
        collector = MetricsCollector()

        for i in range(5):
            collector.add(
                ChatMetrics(
                    model=f'model-{i}',
                    latency_ms=100.0 + i * 10,
                    success=False,
                    error_message=f'Error {i}',
                )
            )

        summary = collector.get_summary()

        assert summary['total_requests'] == 5
        assert summary['successful'] == 0
        assert summary['failed'] == 5
        assert summary['success_rate'] == 0.0

    def test_summary_calculates_correct_averages(self):
        collector = MetricsCollector()

        latencies = [100.0, 200.0, 300.0, 400.0, 500.0]
        for lat in latencies:
            collector.add(ChatMetrics(model='test', latency_ms=lat))

        summary = collector.get_summary()

        assert summary['avg_latency_ms'] == 300.0
        assert summary['min_latency_ms'] == 100.0
        assert summary['max_latency_ms'] == 500.0

    # assertion-reduction-reason: exact value makes presence check redundant.
    def test_collector_max_metrics_constant_defined(self):
        assert MetricsCollector.MAX_METRICS == 10000

    def test_add_and_export_large_dataset(self):
        collector = MetricsCollector(max_metrics=1000)

        for i in range(1000):
            collector.add(
                ChatMetrics(
                    model=f'model-{i % 10}',
                    latency_ms=100.0 + (i % 100),
                    tokens_used=50 + (i % 50),
                    success=(i % 3 != 0),
                )
            )

        json_str = collector.export_json()
        assert len(json_str) > 0

        summary = collector.get_summary()
        assert summary['total_requests'] == 1000
        assert summary['successful'] > 0
        assert summary['failed'] > 0

    def test_metrics_timestamp_format_in_dict(self):
        from datetime import datetime

        metrics = ChatMetrics(model='test', latency_ms=100.0)
        result = metrics.to_dict()

        timestamp_str = result['timestamp']
        assert isinstance(timestamp_str, str)
        parsed = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed, datetime)
