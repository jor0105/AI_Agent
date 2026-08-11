from unittest.mock import Mock

import pytest

from createagents.presentation.cli.application.chat_cli_app import (
    ChatCLIApplication,
)
from createagents.presentation.cli.commands import (
    ChatCommandHandler,
    ClearCommandHandler,
    ConfigsCommandHandler,
    HelpCommandHandler,
    MetricsCommandHandler,
    ToolsCommandHandler,
)


@pytest.mark.unit
class TestChatCLIApplication:
    def test_scenario_initializes_command_registry_order(self):
        app = ChatCLIApplication(agent=Mock())

        handlers = app._registry.get_all_handlers()
        handler_types = [type(handler) for handler in handlers]

        assert handler_types == [
            HelpCommandHandler,
            MetricsCommandHandler,
            ConfigsCommandHandler,
            ToolsCommandHandler,
            ClearCommandHandler,
            ChatCommandHandler,
        ]

    def test_scenario_exit_command_detection(self):
        app = ChatCLIApplication(agent=Mock())

        assert app._is_exit_command('exit') is True
        assert app._is_exit_command('  QUIT  ') is True
        assert app._is_exit_command('continue') is False
        assert app._is_exit_command('') is False
