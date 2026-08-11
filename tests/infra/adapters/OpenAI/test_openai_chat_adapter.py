from unittest.mock import AsyncMock, Mock, patch

import pytest

from createagents.infra.adapters.OpenAI.openai_chat_adapter import (
    OpenAIChatAdapter,
)

IA_OPENAI_TEST_1: str = 'gpt-5-nano'


@pytest.mark.unit
class TestOpenAIChatAdapter:
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIClient'
    )
    def test_initialization_success(
        self, mock_client_cls, mock_stream_cls, mock_handler_cls
    ):
        adapter = OpenAIChatAdapter()

        assert adapter is not None
        mock_client_cls.assert_called_once()
        mock_stream_cls.assert_not_called()
        mock_handler_cls.assert_not_called()

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIClient'
    )
    @pytest.mark.asyncio
    async def test_chat_delegates_to_handler(
        self, mock_client_cls, mock_stream_cls, mock_handler_cls
    ):
        mock_handler = AsyncMock()
        mock_handler_cls.return_value = mock_handler
        mock_handler.execute_tool_loop.return_value = 'Response'

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            config={},
            tools=None,
            user_ask='Ask',
            history=[],
        )

        assert response == 'Response'
        mock_handler.execute_tool_loop.assert_called_once()
        mock_stream_cls.assert_not_called()

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIClient'
    )
    @pytest.mark.asyncio
    async def test_chat_delegates_to_stream_handler(
        self, mock_client_cls, mock_stream_cls, mock_handler_cls
    ):
        mock_stream_handler = Mock()
        mock_stream_cls.return_value = mock_stream_handler
        mock_stream_handler.handle_stream.return_value = iter(['Hello'])

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            config={'stream': True},
            tools=None,
            user_ask='Ask',
            history=[],
        )

        assert list(response) == ['Hello']
        mock_stream_handler.handle_stream.assert_called_once()
        mock_handler_cls.assert_not_called()

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.OpenAIClient'
    )
    def test_get_metrics(
        self, mock_client_cls, mock_stream_cls, mock_handler_cls
    ):
        adapter = OpenAIChatAdapter()

        # Inject metrics manually since we mocked the handlers that usually populate them
        metrics_list = adapter._OpenAIChatAdapter__metrics
        metrics_list.append(Mock())

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
