from unittest.mock import Mock, patch

import pytest

from createagents.presentation.cli.commands.help_command import (
    HelpCommandHandler,
)


@pytest.mark.unit
class TestHelpCommandHandler:
    def test_scenario_can_handle_aliases(self):
        renderer = Mock()
        handler = HelpCommandHandler(renderer)

        assert handler.can_handle('/help') is True
        assert handler.can_handle('help') is True
        assert handler.can_handle('other') is False

    def test_scenario_execute_formats_message(self):
        renderer = Mock()
        handler = HelpCommandHandler(renderer)

        with patch(
            'createagents.presentation.cli.commands.base_command.MarkdownTerminalFormatter.format',
            return_value='formatted-help',
        ) as mock_formatter:
            handler.execute(Mock(), '/help')

        mock_formatter.assert_called_once()
        renderer.render_system_message.assert_called_once_with(
            'formatted-help'
        )
