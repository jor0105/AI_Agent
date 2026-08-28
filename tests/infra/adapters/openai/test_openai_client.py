from unittest.mock import AsyncMock, Mock, patch

import pytest

from createagents.infra.adapters.openai.openai_client import OpenAIClient
from createagents.infra.config import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT

IA_OPENAI_TEST_1: str = 'gpt-5-nano'
IA_OPENAI_TEST_2: str = 'gpt-5-mini'


@pytest.mark.unit
class TestOpenAIClient:
    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    def test_initialization_success(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        client = OpenAIClient()

        assert client is not None
        mock_get_api_key.assert_called_once_with('OPENAI_API_KEY')
        mock_get_client.assert_called_once_with(
            'test-api-key',
            timeout=DEFAULT_TIMEOUT,
            max_retries=DEFAULT_MAX_RETRIES,
        )

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    @pytest.mark.asyncio
    async def test_call_api_constructs_messages_correctly(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'
        mock_client = Mock()
        mock_client.responses = Mock()
        mock_client.responses.create = AsyncMock()
        mock_get_client.return_value = mock_client

        client = OpenAIClient()

        messages = [
            {'role': 'system', 'content': 'System instruction'},
            {'role': 'user', 'content': 'Previous message'},
            {'role': 'user', 'content': 'User question'},
        ]

        await client.call_api(
            model=IA_OPENAI_TEST_2,
            instructions='System instruction',
            messages=messages,
            config={},
        )

        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs['input'] == messages
        assert call_args.kwargs['model'] == IA_OPENAI_TEST_2

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    @pytest.mark.asyncio
    async def test_call_api_handles_config_mapping(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'
        mock_client = Mock()
        mock_client.responses = Mock()
        mock_client.responses.create = AsyncMock()
        mock_get_client.return_value = mock_client

        client = OpenAIClient()

        config = {
            'think': 'high',
            'max_tokens': 1000,
            'temperature': 0.7,
            'stream': True,
        }

        await client.call_api(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            messages=[],
            config=config,
        )

        call_args = mock_client.responses.create.call_args
        kwargs = call_args.kwargs

        assert kwargs['reasoning'] == {'effort': 'high'}
        assert kwargs['max_output_tokens'] == 1000
        assert kwargs['temperature'] == 0.7
        assert kwargs['stream'] is True
        # Ensure original config keys are removed/mapped
        assert 'max_tokens' not in kwargs
        assert 'think' not in kwargs

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    @pytest.mark.asyncio
    async def test_call_api_passes_tools(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'
        mock_client = Mock()
        mock_client.responses = Mock()
        mock_client.responses.create = AsyncMock()
        mock_get_client.return_value = mock_client

        client = OpenAIClient()

        tools = [{'type': 'function', 'function': {'name': 'test_tool'}}]

        await client.call_api(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            messages=[],
            config={},
            tools=tools,
        )

        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs['tools'] == tools
