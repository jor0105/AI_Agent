from unittest.mock import Mock

import pytest

from createagents.presentation.cli.application.command_registry import (
    CommandRegistry,
)
from createagents.presentation.cli.commands import CommandHandler


@pytest.mark.unit
class TestCommandRegistry:
    def test_scenario_register_and_find_handler(self):
        registry = CommandRegistry()
        handler1 = Mock(spec=CommandHandler)
        handler2 = Mock(spec=CommandHandler)
        handler1.can_handle.return_value = False
        handler2.can_handle.side_effect = lambda user_input: (
            user_input == '/metrics'
        )

        registry.register(handler1)
        registry.register(handler2)

        found = registry.find_handler('/metrics')

        assert found is handler2
        handler1.can_handle.assert_called_once_with('/metrics')
        handler2.can_handle.assert_called_once_with('/metrics')

    def test_scenario_find_handler_returns_none(self):
        registry = CommandRegistry()
        handler = Mock(spec=CommandHandler)
        handler.can_handle.return_value = False

        registry.register(handler)
        result = registry.find_handler('/unknown')

        assert result is None
        handler.can_handle.assert_called_once_with('/unknown')

    def test_scenario_get_all_handlers_returns_copy(self):
        registry = CommandRegistry()
        handler = Mock(spec=CommandHandler)
        registry.register(handler)

        handlers = registry.get_all_handlers()
        handlers.clear()

        assert registry.get_all_handlers() == [handler]

    def test_scenario_clear_registry(self):
        registry = CommandRegistry()
        handler = Mock(spec=CommandHandler)
        registry.register(handler)

        registry.clear()

        assert registry.get_all_handlers() == []
