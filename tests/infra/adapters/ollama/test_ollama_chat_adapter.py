from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from createagents.application import ChatRepository
from createagents.domain import ChatException
from createagents.infra import OllamaChatAdapter
from tests.test_constants import OLLAMA_MODEL_PHI

# allow-assertion-reduction: Removed Ollama stop-process lifecycle cases target retired adapter behavior.


def _mock_response(
    content: str | None = 'Response',
    tool_calls: object = None,
    get_return: object = None,
) -> MagicMock:
    m = MagicMock()
    m.message = MagicMock()
    m.message.content = content
    m.message.tool_calls = tool_calls

    def get_side_effect(key: object, default: object = None) -> object:
        if get_return is not None:
            return get_return
        return default

    m.get.side_effect = get_side_effect
    return m


@pytest.mark.unit
class TestOllamaChatAdapter:
    # assertion-reduction-reason: public behavior replaces private checks.
    def test_initialization(self):
        adapter = OllamaChatAdapter()

        assert adapter is not None
        assert isinstance(adapter, ChatRepository)
        assert adapter.get_metrics() == []

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_valid_input(self, mock_call_api):
        mock_call_api.return_value = _mock_response(
            content='Ollama response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Be helpful',
            config={},
            tools=None,
            history=[],
            user_ask='Hello',
        )

        assert response == 'Ollama response'
        mock_call_api.assert_called_once()

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_constructs_messages_correctly(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='System instruction',
            config={},
            tools=None,
            history=[{'role': 'user', 'content': 'Previous message'}],
            user_ask='User question',
        )

        call_args = mock_chat.call_args
        messages = call_args.args[1]

        assert len(messages) == 3
        assert messages[0] == {
            'role': 'system',
            'content': 'System instruction',
        }
        assert messages[1] == {'role': 'user', 'content': 'Previous message'}
        assert messages[2] == {'role': 'user', 'content': 'User question'}

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_empty_history(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Instructions',
            config={},
            tools=None,
            history=[],
            user_ask='Question',
        )

        call_args = mock_chat.call_args
        messages = call_args.args[1]

        assert len(messages) == 2

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_multiple_history_items(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        history = [
            {'role': 'user', 'content': 'Msg 1'},
            {'role': 'assistant', 'content': 'Reply 1'},
            {'role': 'user', 'content': 'Msg 2'},
            {'role': 'assistant', 'content': 'Reply 2'},
        ]

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Instructions',
            config={},
            tools=None,
            history=history,
            user_ask='New question',
        )

        call_args = mock_chat.call_args
        messages = call_args.args[1]

        assert len(messages) == 6

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_passes_correct_model(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        assert call_args.args[0] == OLLAMA_MODEL_PHI

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_empty_response_raises_error(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match='Ollama returned multiple empty responses'
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_none_response_raises_error(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content=None, tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match='Ollama returned multiple empty responses'
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_missing_message_key_raises_error(self, mock_chat):
        class BadMessage:
            tool_calls = None

            @property
            def content(self):
                raise AttributeError(
                    "'dict' object has no attribute 'content'"
                )

        mock_response = MagicMock()
        mock_response.message = BadMessage()
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException,
            match='An error occurred while communicating with Ollama',
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_attribute_error_raises_chat_exception(
        self, mock_chat
    ):
        class BadResponse:
            @property
            def message(self):
                raise AttributeError(
                    "'ChatResponse' object has no attribute 'message'"
                )

        mock_chat.return_value = BadResponse()

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException,
            match='An error occurred while communicating with Ollama',
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_type_error_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = TypeError('Invalid type')

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException,
            match='An error occurred while communicating with Ollama',
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_generic_exception_raises_chat_exception(
        self, mock_chat
    ):
        mock_chat.side_effect = RuntimeError('Connection error')

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException,
            match='An error occurred while communicating with Ollama',
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_preserves_original_error(self, mock_chat):
        original_error = RuntimeError('Original error')
        mock_chat.side_effect = original_error

        adapter = OllamaChatAdapter()

        try:
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )
        except ChatException as e:
            assert e.original_error is original_error

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_propagates_chat_exception(self, mock_chat):
        original_exception = ChatException('Original chat error')
        mock_chat.side_effect = original_exception

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException) as exc_info:
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

        assert exc_info.value is original_exception

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_special_characters(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Resposta com 你好 e emojis 🎉',
            tool_calls=None,
            get_return=None,
        )

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test 你好',
            config={},
            tools=None,
            history=[],
            user_ask='Question 🎉',
        )

        assert isinstance(response, str)
        assert '你好' in response
        assert '🎉' in response

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_multiline_content(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Line 1\nLine 2\nLine 3', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Multi\nline\ninstructions',
            config={},
            tools=None,
            history=[],
            user_ask='Multi\nline\nquestion',
        )

        assert isinstance(response, str)
        assert '\n' in response
        assert 'Line 1' in response

    def test_adapter_implements_chat_repository_interface(self):
        from createagents.application.interfaces.chat_repository import (
            ChatRepository,
        )

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)
        assert callable(adapter.chat)

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_collects_metrics_on_success(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Success response', tool_calls=None, get_return=100
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Test',
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == OLLAMA_MODEL_PHI
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 200
        assert metrics[0].latency_ms > 0

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_collects_metrics_on_failure(self, mock_chat):
        mock_chat.side_effect = RuntimeError('Test error')

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == OLLAMA_MODEL_PHI
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_collects_multiple_metrics(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Test 1',
        )

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Test 2',
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == OLLAMA_MODEL_PHI
        assert metrics[1].model == OLLAMA_MODEL_PHI

    def test_get_metrics_returns_copy(self):
        adapter = OllamaChatAdapter()

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        assert metrics1 is not metrics2

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_empty_string_in_history(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        history = [
            {'role': 'user', 'content': ''},
            {'role': 'assistant', 'content': 'Previous response'},
        ]

        response = await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=history,
            user_ask='New question',
        )

        assert response == 'Response'
        call_args = mock_chat.call_args
        messages = call_args.args[1]
        assert len(messages) == 4

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_long_history(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        history = []
        for i in range(25):
            history.append({'role': 'user', 'content': f'Message {i}'})
            history.append({'role': 'assistant', 'content': f'Reply {i}'})

        response = await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=history,
            user_ask='Final question',
        )

        assert response == 'Response'
        call_args = mock_chat.call_args
        messages = call_args.args[1]
        assert len(messages) == 52

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_config_parameter(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        config = {'temperature': 0.7, 'max_tokens': 1000, 'top_p': 0.9}

        response = await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config=config,
            tools=None,
            history=[],
            user_ask='Test',
        )

        assert response == 'Response'

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_key_error_raises_chat_exception(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.tool_calls = None
        type(mock_response.message).content = property(
            lambda self: (_ for _ in ()).throw(KeyError('test_key'))
        )
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException,
            match='An error occurred while communicating with Ollama',
        ):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_metrics_contain_error_message_on_empty_response(
        self, mock_chat
    ):
        mock_chat.return_value = _mock_response(
            content='', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException):
            await adapter.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].error_message is not None
        assert metrics[0].success is False

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_passes_temperature_config(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={'temperature': 0.7},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        assert call_args.args[2]['temperature'] == 0.7

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_passes_max_tokens_as_num_predict(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={'max_tokens': 500},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        assert call_args.args[2]['max_tokens'] == 500

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_passes_top_p_config(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={'top_p': 0.9},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        assert call_args.args[2]['top_p'] == 0.9

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_passes_all_configs(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 500,
            'top_p': 0.9,
        }

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config=config,
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        expected_config = {
            'temperature': 0.7,
            'max_tokens': 500,
            'top_p': 0.9,
        }
        assert call_args.args[2] == expected_config

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_empty_config_does_not_pass_options(
        self, mock_chat
    ):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        assert call_args.args[2] == {}
        assert call_args.args[0] == OLLAMA_MODEL_PHI
        assert isinstance(call_args.args[1], list)

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_none_instructions_omits_system_message(
        self, mock_chat
    ):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions=None,
            config={},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        messages = call_args.args[1]

        assert len(messages) == 1
        assert messages[0] == {'role': 'user', 'content': 'Test'}

    @patch(
        'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_chat_with_whitespace_only_instructions(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content='Response', tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=OLLAMA_MODEL_PHI,
            instructions='   \n\t  ',
            config={},
            tools=None,
            history=[],
            user_ask='Test',
        )

        call_args = mock_chat.call_args
        messages = call_args.args[1]

        assert len(messages) == 1
        assert messages[0]['role'] == 'user'

    def test_initialization_reads_environment_variables(self):
        with patch(
            'createagents.infra.adapters.ollama.ollama_client.EnvironmentConfig.get_env'
        ) as mock_get_env:
            mock_get_env.side_effect = lambda key, default: {
                'OLLAMA_HOST': 'http://custom-host:11434',
                'OLLAMA_MAX_RETRIES': '5',
            }.get(key, default)

            OllamaChatAdapter()

            assert mock_get_env.call_count >= 2
