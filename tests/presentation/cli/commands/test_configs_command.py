from unittest.mock import Mock, patch

import pytest

from createagents.presentation.cli.commands.configs_command import (
    ConfigsCommandHandler,
)


@pytest.mark.unit
class TestConfigsCommandHandler:
    def test_scenario_can_handle_aliases(self):
        renderer = Mock()
        handler = ConfigsCommandHandler(renderer)

        assert handler.can_handle('/configs') is True
        assert handler.can_handle('get_configs') is True
        assert handler.can_handle('/unknown') is False

    def test_scenario_execute_formats_configs(self):
        renderer = Mock()
        handler = ConfigsCommandHandler(renderer)
        agent = Mock()
        agent.get_configs.return_value = {
            'provider': 'openai',
            'history': [
                {
                    'role': 'user',
                    'content': 'Hello world message exceeding fifty characters for preview testing',
                },
                {'role': 'assistant', 'content': 'Response text'},
            ],
        }

        with patch(
            'createagents.presentation.cli.commands.base_command.MarkdownTerminalFormatter.format',
            return_value='formatted-configs',
        ) as mock_formatter:
            handler.execute(agent, '/configs')

        agent.get_configs.assert_called_once_with()
        args, _ = mock_formatter.call_args
        assert 'Agent Configuration' in args[0]
        assert 'history' in args[0]
        renderer.render_system_message.assert_called_once_with(
            'formatted-configs'
        )
