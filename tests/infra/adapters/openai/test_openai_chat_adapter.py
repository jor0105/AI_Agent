from unittest.mock import AsyncMock, Mock, patch

import pytest

from createagents.domain import ChatMetrics
from createagents.infra.adapters.openai.openai_chat_adapter import (
    OpenAIChatAdapter,
)

IA_OPENAI_TEST_1: str = 'gpt-5-nano'


@pytest.mark.unit
class TestOpenAIChatAdapter:
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIClient'
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
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIClient'
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
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIClient'
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

    @pytest.mark.asyncio
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIStreamHandler'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_chat_adapter.OpenAIClient'
    )
    async def test_get_metrics(
        self, mock_client_cls, mock_stream_cls, mock_handler_cls
    ):
        adapter = OpenAIChatAdapter()
        assert adapter.get_metrics() == []

        async def fake_execute(*args, **kwargs):
            metrics_list = mock_handler_cls.call_args[0][1]
            metrics_list.append(
                ChatMetrics(model='gpt-5', latency_ms=10.0, success=True)
            )
            return 'Response'

        mock_handler = Mock()
        mock_handler.execute_tool_loop = fake_execute
        mock_handler_cls.return_value = mock_handler

        await adapter.chat(
            model='gpt-5',
            instructions='test',
            config=None,
            tools=None,
            history=[],
            user_ask='hi',
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'gpt-5'
