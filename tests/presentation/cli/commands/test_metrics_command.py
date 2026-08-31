from unittest.mock import Mock, patch

import pytest

from createagents.domain import ChatMetrics
from createagents.presentation.cli.commands.metrics_command import (
    MetricsCommandHandler,
)
from tests.test_constants import OPENAI_MODEL_MINI


@pytest.mark.unit
class TestMetricsCommandHandler:
    def test_scenario_can_handle_aliases(self):
        renderer = Mock()
        handler = MetricsCommandHandler(renderer)

        assert handler.can_handle('/metrics') is True
        assert handler.can_handle('get_metrics') is True
        assert handler.can_handle('other') is False

    def test_scenario_execute_without_metrics(self):
        renderer = Mock()
        agent = Mock()
        agent.get_metrics.return_value = []
        handler = MetricsCommandHandler(renderer)

        handler.execute(agent, '/metrics')

        agent.get_metrics.assert_called_once_with()
        renderer.render_system_message.assert_called_once()
        args, _ = renderer.render_system_message.call_args
        assert 'No metrics available' in args[0]

    def test_scenario_execute_with_metrics(self):
        renderer = Mock()
        agent = Mock()
        agent.get_metrics.return_value = [
            ChatMetrics(
                model=OPENAI_MODEL_MINI,
                latency_ms=150.0,
                tokens_used=80,
                prompt_tokens=30,
                completion_tokens=50,
            )
        ]
        handler = MetricsCommandHandler(renderer)

        with patch(
            'createagents.presentation.cli.commands.base_command.MarkdownTerminalFormatter.format',
            return_value='formatted-metrics',
        ) as mock_formatter:
            handler.execute(agent, '/metrics')

        agent.get_metrics.assert_called_once_with()
        args, _ = mock_formatter.call_args
        assert 'Performance Metrics' in args[0]
        assert OPENAI_MODEL_MINI in args[0]
        renderer.render_system_message.assert_called_once_with(
            'formatted-metrics'
        )
