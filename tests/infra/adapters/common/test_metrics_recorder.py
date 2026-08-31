import time
from unittest.mock import Mock

import pytest

from createagents.domain import ChatMetrics
from createagents.infra.adapters.common.metrics_recorder import (
    OllamaMetricsRecorder,
    OpenAIMetricsRecorder,
    ProviderUsage,
)
from tests.test_constants import OPENAI_MODEL_MINI

# allow-assertion-reduction: Generic provider cases were replaced by provider-specific recorder coverage below.


@pytest.mark.unit
class TestRecorderBaseBehaviour:
    """Shared behaviour, exercised through a concrete recorder."""

    def test_starts_with_an_empty_metrics_list(self):
        assert OpenAIMetricsRecorder().get_metrics() == []

    def test_appends_to_an_injected_list(self):
        shared: list[ChatMetrics] = []
        recorder = OpenAIMetricsRecorder(shared)

        recorder.record_error_metrics('m', time.time(), 'boom')

        assert len(shared) == 1

    def test_records_error_metrics(self):
        recorder = OpenAIMetricsRecorder()

        recorder.record_error_metrics(
            model='test-model',
            start_time=time.time(),
            error=ValueError('Test error'),
        )

        metrics = recorder.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'test-model'
        assert metrics[0].success is False
        assert metrics[0].error_message == 'Test error'
        assert metrics[0].latency_ms >= 0

    def test_falsy_error_becomes_a_readable_message(self):
        recorder = OpenAIMetricsRecorder()

        recorder.record_error_metrics('m', time.time(), None)

        assert recorder.get_metrics()[0].error_message == 'Unknown error'

    def test_get_metrics_returns_a_copy(self):
        recorder = OpenAIMetricsRecorder()
        recorder.record_error_metrics('test', time.time(), 'error')

        first = recorder.get_metrics()
        second = recorder.get_metrics()

        assert first == second
        assert first is not second

    def test_records_in_call_order(self):
        recorder = OpenAIMetricsRecorder()
        start = time.time()

        recorder.record_success_metrics('model1', start, Mock())
        recorder.record_error_metrics('model2', start, 'err')
        recorder.record_success_metrics('model3', start, Mock())

        assert [m.model for m in recorder.get_metrics()] == [
            'model1',
            'model2',
            'model3',
        ]


@pytest.mark.unit
class TestOpenAIMetricsRecorder:
    def test_reads_token_counts_from_usage(self):
        response = Mock()
        response.usage = Mock(
            spec=['total_tokens', 'prompt_tokens', 'completion_tokens'],
            total_tokens=100,
            prompt_tokens=50,
            completion_tokens=50,
        )
        recorder = OpenAIMetricsRecorder()

        recorder.record_success_metrics(
            OPENAI_MODEL_MINI, time.time(), response
        )

        metrics = recorder.get_metrics()[0]
        assert metrics.model == OPENAI_MODEL_MINI
        assert metrics.tokens_used == 100
        assert metrics.prompt_tokens == 50
        assert metrics.completion_tokens == 50
        assert metrics.success is True

    def test_reads_token_counts_from_responses_api_usage(self):
        response = Mock()
        response.usage = Mock(
            spec=['total_tokens', 'input_tokens', 'output_tokens'],
            total_tokens=75,
            input_tokens=40,
            output_tokens=35,
        )
        recorder = OpenAIMetricsRecorder()

        recorder.record_success_metrics(
            OPENAI_MODEL_MINI, time.time(), response
        )

        metrics = recorder.get_metrics()[0]
        assert metrics.model == OPENAI_MODEL_MINI
        assert metrics.tokens_used == 75
        assert metrics.prompt_tokens == 40
        assert metrics.completion_tokens == 35
        assert metrics.success is True

    def test_calculates_total_tokens_when_missing(self):
        response = Mock()
        response.usage = Mock(
            spec=['input_tokens', 'output_tokens'],
            input_tokens=25,
            output_tokens=15,
        )
        recorder = OpenAIMetricsRecorder()

        usage = recorder._extract_usage(response)

        assert usage.tokens_used == 40
        assert usage.prompt_tokens == 25
        assert usage.completion_tokens == 15

    def test_a_response_without_usage_yields_no_token_counts(self):
        recorder = OpenAIMetricsRecorder()

        usage = recorder._extract_usage(Mock(spec=[]))

        assert usage == ProviderUsage()

    def test_openai_reports_no_durations(self):
        response = Mock()
        response.usage = Mock(
            total_tokens=1, prompt_tokens=1, completion_tokens=0
        )
        recorder = OpenAIMetricsRecorder()

        recorder.record_success_metrics(
            OPENAI_MODEL_MINI, time.time(), response
        )

        metrics = recorder.get_metrics()[0]
        assert metrics.load_duration_ms is None
        assert metrics.prompt_eval_duration_ms is None
        assert metrics.eval_duration_ms is None


@pytest.mark.unit
class TestOllamaMetricsRecorder:
    def test_reads_counts_and_converts_nanosecond_durations(self):
        response = {
            'prompt_eval_count': 30,
            'eval_count': 20,
            'load_duration': 1_000_000,
            'prompt_eval_duration': 2_000_000,
            'eval_duration': 3_000_000,
        }
        recorder = OllamaMetricsRecorder()

        recorder.record_success_metrics('llama2', time.time(), response)

        metrics = recorder.get_metrics()[0]
        assert metrics.model == 'llama2'
        assert metrics.tokens_used == 50
        assert metrics.prompt_tokens == 30
        assert metrics.completion_tokens == 20
        assert metrics.load_duration_ms == 1.0
        assert metrics.prompt_eval_duration_ms == 2.0
        assert metrics.eval_duration_ms == 3.0

    def test_empty_response_yields_zero_tokens_and_no_durations(self):
        usage = OllamaMetricsRecorder()._extract_usage({})

        assert usage == ProviderUsage(
            tokens_used=0, prompt_tokens=0, completion_tokens=0
        )

    def test_missing_durations_stay_none(self):
        usage = OllamaMetricsRecorder()._extract_usage(
            {'prompt_eval_count': 1, 'eval_count': 2}
        )

        assert usage.load_duration_ms is None
        assert usage.prompt_eval_duration_ms is None
        assert usage.eval_duration_ms is None
