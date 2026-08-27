from unittest.mock import Mock, patch

import pytest

from createagents.presentation.cli.commands.tools_command import (
    ToolsCommandHandler,
)


@pytest.mark.unit
class TestToolsCommandHandler:
    def test_scenario_can_handle_aliases(self):
        renderer = Mock()
        handler = ToolsCommandHandler(renderer)

        assert handler.can_handle('/tools') is True
        assert handler.can_handle('get_tools') is True
        assert handler.can_handle('/unknown') is False

    def test_scenario_execute_without_tools(self):
        renderer = Mock()
        agent = Mock()
        agent.get_all_available_tools.return_value = {}
        handler = ToolsCommandHandler(renderer)

        with patch(
            'createagents.presentation.cli.commands.base_command.MarkdownTerminalFormatter.format',
            return_value='no-tools',
        ) as mock_formatter:
            handler.execute(agent, '/tools')

        agent.get_all_available_tools.assert_called_once_with()
        args, _ = mock_formatter.call_args
        assert 'No tools configured' in args[0]
        renderer.render_system_message.assert_called_once_with('no-tools')

    def test_scenario_execute_with_tools(self):
        renderer = Mock()
        agent = Mock()
        agent.get_all_available_tools.return_value = {
            'browser': 'Search the web',
            'calculator': 'Perform math operations',
        }
        handler = ToolsCommandHandler(renderer)

        with patch(
            'createagents.presentation.cli.commands.base_command.MarkdownTerminalFormatter.format',
            return_value='tools-list',
        ) as mock_formatter:
            handler.execute(agent, '/tools')

        agent.get_all_available_tools.assert_called_once_with()
        args, _ = mock_formatter.call_args
        assert 'browser' in args[0]
        assert 'calculator' in args[0]
        renderer.render_system_message.assert_called_once_with('tools-list')
