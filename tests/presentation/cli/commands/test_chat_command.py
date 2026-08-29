import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from createagents.application import StreamingResponseDTO
from createagents.presentation.cli.commands.chat_command import (
    ChatCommandHandler,
)


def _run_coroutine(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.mark.unit
class TestChatCommandHandler:
    def test_scenario_can_handle_only_non_empty_inputs(self):
        handler = ChatCommandHandler(Mock())

        assert handler.can_handle('hello') is True
        assert handler.can_handle('   ') is False

    def test_scenario_execute_non_streaming_flow(self):
        renderer = Mock()
        renderer.render_ai_message_streaming = AsyncMock()
        agent = Mock()
        agent.chat = AsyncMock(return_value='raw response')
        handler = ChatCommandHandler(renderer)

        with (
            patch(
                'createagents.presentation.cli.commands.chat_command.MarkdownTerminalFormatter.format',
                return_value='formatted',
            ) as mock_formatter,
            patch(
                'asyncio.run',
                side_effect=_run_coroutine,
            ),
        ):
            handler.execute(agent, 'Hello')

        agent.chat.assert_awaited_once_with('Hello')
        renderer.render_ai_message.assert_called_once_with('formatted')
        renderer.render_ai_message_streaming.assert_not_awaited()
        renderer.clear_thinking_indicator.assert_called_once_with()
        mock_formatter.assert_called_once_with('raw response')

    def test_scenario_execute_streaming_flow(self):
        async def token_generator() -> AsyncGenerator[str, None]:
            yield 'Hello'
            yield ' World'

        renderer = Mock()
        renderer.render_ai_message_streaming = AsyncMock()
        agent = Mock()
        streaming_response = StreamingResponseDTO(token_generator())
        agent.chat = AsyncMock(return_value=streaming_response)
        handler = ChatCommandHandler(renderer)

        with (
            patch(
                'createagents.presentation.cli.commands.chat_command.MarkdownTerminalFormatter.format'
            ) as mock_formatter,
            patch(
                'asyncio.run',
                side_effect=_run_coroutine,
            ),
        ):
            handler.execute(agent, 'stream this')

        renderer.render_ai_message_streaming.assert_awaited_once_with(
            streaming_response
        )
        mock_formatter.assert_not_called()

    def test_scenario_execute_handles_errors(self):
        renderer = Mock()
        renderer.render_ai_message_streaming = AsyncMock()
        agent = Mock()
        agent.chat = AsyncMock(side_effect=RuntimeError('boom'))
        handler = ChatCommandHandler(renderer)

        with patch('asyncio.run', side_effect=_run_coroutine):
            handler.execute(agent, 'fail please')

        renderer.clear_thinking_indicator.assert_called_once_with()
        renderer.render_ai_message.assert_called_once()
        args, _ = renderer.render_ai_message.call_args
        assert args[0] == 'Error: boom'
