from unittest.mock import Mock

import pytest

from createagents.presentation.cli.commands.clear_command import (
    ClearCommandHandler,
)


@pytest.mark.unit
class TestClearCommandHandler:
    def test_scenario_can_handle_aliases(self):
        renderer = Mock()
        handler = ClearCommandHandler(renderer)

        assert handler.can_handle('/clear') is True
        assert handler.can_handle('clear_history') is True
        assert handler.can_handle('/unknown') is False

    def test_scenario_execute_clears_history(self):
        renderer = Mock()
        agent = Mock()
        handler = ClearCommandHandler(renderer)

        handler.execute(agent, '/clear')

        agent.clear_history.assert_called_once_with()
        renderer.render_success_message.assert_called_once()
