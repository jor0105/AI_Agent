from typing import Any, cast

import pytest

from createagents.domain import ChatMetrics
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


class FakeRenderer:
    """Renderer double that records visible CLI events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Any]] = []

    def render_welcome_screen(self) -> None:
        self.events.append(('welcome', None))

    def render_prompt(self) -> None:
        self.events.append(('prompt', None))

    def render_input_indicator(self) -> None:
        self.events.append(('input_indicator', None))

    def clear_input_lines(self, count: int) -> None:
        self.events.append(('clear_input_lines', count))

    def render_goodbye(self) -> None:
        self.events.append(('goodbye', None))

    def render_interrupt(self) -> None:
        self.events.append(('interrupt', None))

    def render_error(self, message: str) -> None:
        self.events.append(('error', message))


class FakeInputReader:
    """Input double that yields strings or raises a controlled exception."""

    def __init__(self, events: list[str | BaseException]) -> None:
        self._events = iter(events)
        self.prompts: list[str] = []

    def read_user_input(self, prompt: str) -> str:
        self.prompts.append(prompt)
        event = next(self._events)
        if isinstance(event, BaseException):
            raise event
        return event


class FakeHandler:
    """Command handler double with optional controlled failure."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[object, str]] = []

    def execute(self, agent: object, user_input: str) -> None:
        self.calls.append((agent, user_input))
        if self.error is not None:
            raise self.error


class FakeRegistry:
    """Registry double that returns only explicitly registered handlers."""

    def __init__(self, handlers: dict[str, FakeHandler]) -> None:
        self.handlers = handlers
        self.requests: list[str] = []

    def find_handler(self, user_input: str) -> FakeHandler | None:
        self.requests.append(user_input)
        return self.handlers.get(user_input)


class FakeLogger:
    """Logger double that records generic command-loop failures."""

    def __init__(self) -> None:
        self.exceptions: list[str] = []

    def exception(self, message: str) -> None:
        self.exceptions.append(message)


class FakeAgent:
    """Minimal facade implementation retained only for CLI orchestration."""

    async def chat(self, message: str) -> str:
        return ''

    def get_configs(self) -> dict[str, Any]:
        return {}

    def get_all_available_tools(self) -> dict[str, str]:
        return {}

    def clear_history(self) -> None:
        return None

    def get_metrics(self) -> list[ChatMetrics]:
        return []


def _configured_app(
    inputs: list[str | BaseException],
    handlers: dict[str, FakeHandler] | None = None,
) -> tuple[
    ChatCLIApplication,
    FakeAgent,
    FakeRenderer,
    FakeInputReader,
    FakeRegistry,
    FakeLogger,
]:
    """Build an app whose runtime collaborators are deterministic doubles."""
    agent = FakeAgent()
    app = ChatCLIApplication(agent=agent)
    renderer = FakeRenderer()
    input_reader = FakeInputReader(inputs)
    registry = FakeRegistry(handlers or {})
    logger = FakeLogger()
    runtime_app = cast(Any, app)
    runtime_app._renderer = renderer
    runtime_app._input_reader = input_reader
    runtime_app._registry = registry
    runtime_app._logger = logger
    return app, agent, renderer, input_reader, registry, logger


@pytest.mark.unit
class TestChatCLIApplication:
    def test_initializes_command_registry_in_required_order(self):
        app = ChatCLIApplication(agent=FakeAgent())

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

    def test_exit_command_detection(self):
        app = ChatCLIApplication(agent=FakeAgent())

        assert app._is_exit_command('exit') is True
        assert app._is_exit_command('  QUIT  ') is True
        assert app._is_exit_command('continue') is False
        assert app._is_exit_command('') is False

    @pytest.mark.parametrize('command', ['exit', 'quit'])
    def test_run_renders_welcome_and_exits_for_exit_commands(self, command):
        app, _, renderer, _, registry, _ = _configured_app([command])

        app.run()

        assert renderer.events[0] == ('welcome', None)
        assert ('goodbye', None) in renderer.events
        assert registry.requests == []

    def test_run_ignores_empty_input(self):
        app, _, renderer, _, registry, _ = _configured_app(['   ', 'exit'])

        app.run()

        clear_events = [
            event
            for event in renderer.events
            if event[0] == 'clear_input_lines'
        ]
        assert registry.requests == []
        assert clear_events == [
            ('clear_input_lines', 2),
            ('clear_input_lines', 2),
        ]

    def test_run_dispatches_to_matching_handler_and_clears_input(self):
        handler = FakeHandler()
        app, agent, renderer, _, registry, _ = _configured_app(
            ['hello', 'exit'], {'hello': handler}
        )

        app.run()

        assert handler.calls == [(agent, 'hello')]
        assert registry.requests == ['hello']
        assert [
            event
            for event in renderer.events
            if event[0] == 'clear_input_lines'
        ] == [('clear_input_lines', 2), ('clear_input_lines', 2)]

    def test_run_renders_error_when_no_handler_is_available(self):
        app, _, renderer, _, registry, _ = _configured_app(
            ['/unknown', 'exit']
        )

        app.run()

        assert registry.requests == ['/unknown']
        assert (
            'error',
            'No handler found for this command.',
        ) in renderer.events
        assert ('goodbye', None) in renderer.events

    def test_run_handles_keyboard_interrupt(self):
        app, _, renderer, _, registry, _ = _configured_app(
            [KeyboardInterrupt()]
        )

        app.run()

        assert registry.requests == []
        assert renderer.events[-1] == ('interrupt', None)
        assert ('goodbye', None) not in renderer.events

    def test_run_handles_eof_with_a_graceful_goodbye(self):
        app, _, renderer, _, registry, logger = _configured_app([EOFError()])

        app.run()

        assert registry.requests == []
        assert renderer.events[-1] == ('goodbye', None)
        assert logger.exceptions == []

    def test_run_renders_handler_error_and_continues(self):
        handler = FakeHandler(RuntimeError('handler failed'))
        app, _, renderer, _, registry, logger = _configured_app(
            ['broken', 'exit'], {'broken': handler}
        )

        app.run()

        assert registry.requests == ['broken']
        assert ('error', 'handler failed') in renderer.events
        assert renderer.events[-1] == ('goodbye', None)
        assert logger.exceptions == ['Unhandled error in CLI command loop']
