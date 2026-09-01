from collections.abc import Iterator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from createagents.infra.adapters.openai.openai_client import OpenAIClient
from createagents.infra.config import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT
from tests.test_constants import OPENAI_MODEL_MINI, OPENAI_MODEL_NANO


@pytest.fixture
def mocked_openai_client() -> Iterator[tuple[OpenAIClient, Mock]]:
    with (
        patch(
            'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key',
            return_value='test-api-key',
        ),
        patch(
            'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
        ) as mock_get_client,
    ):
        mock_client = Mock()
        mock_client.responses = Mock()
        mock_client.responses.create = AsyncMock()
        mock_get_client.return_value = mock_client
        yield OpenAIClient(), mock_client


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

    @pytest.mark.asyncio
    async def test_call_api_constructs_messages_correctly(
        self, mocked_openai_client
    ):
        client, mock_client = mocked_openai_client

        messages = [
            {'role': 'system', 'content': 'System instruction'},
            {'role': 'user', 'content': 'Previous message'},
            {'role': 'user', 'content': 'User question'},
        ]

        await client.call_api(
            model=OPENAI_MODEL_MINI,
            instructions='System instruction',
            messages=messages,
            config={},
        )

        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs['input'] == messages
        assert call_args.kwargs['model'] == OPENAI_MODEL_MINI

    @pytest.mark.asyncio
    async def test_call_api_maps_reasoning_tokens_and_stream(
        self, mocked_openai_client
    ):
        client, mock_client = mocked_openai_client
        config = {
            'think': 'high',
            'max_tokens': 1000,
            'stream': True,
        }

        await client.call_api(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config=config,
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs == {
            'model': OPENAI_MODEL_NANO,
            'instructions': 'Instr',
            'input': [],
            'reasoning': {'effort': 'high'},
            'max_output_tokens': 1000,
            'stream': True,
        }
        assert 'max_tokens' not in kwargs
        assert 'think' not in kwargs

    @pytest.mark.asyncio
    async def test_call_api_preserves_responses_reasoning_object(
        self, mocked_openai_client
    ):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={'reasoning': {'effort': 'low'}},
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs['reasoning'] == {'effort': 'low'}

    @pytest.mark.asyncio
    @pytest.mark.parametrize('max_tokens', [-1, 0])
    async def test_call_api_ignores_non_positive_max_tokens(
        self, mocked_openai_client, max_tokens
    ):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={'max_tokens': max_tokens},
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert 'max_output_tokens' not in kwargs

    @pytest.mark.asyncio
    async def test_call_api_passes_temperature(self, mocked_openai_client):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model='gpt-4o-mini',
            instructions='Instr',
            messages=[],
            config={'temperature': 0.7},
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs == {
            'model': 'gpt-4o-mini',
            'instructions': 'Instr',
            'input': [],
            'temperature': 0.7,
        }

    @pytest.mark.asyncio
    async def test_call_api_passes_top_p(self, mocked_openai_client):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model='gpt-4o-mini',
            instructions='Instr',
            messages=[],
            config={'top_p': 0.9},
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs == {
            'model': 'gpt-4o-mini',
            'instructions': 'Instr',
            'input': [],
            'top_p': 0.9,
        }

    @pytest.mark.asyncio
    async def test_call_api_ignores_ollama_only_top_k(
        self, mocked_openai_client
    ):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={'top_k': 50},
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs == {
            'model': OPENAI_MODEL_NANO,
            'instructions': 'Instr',
            'input': [],
        }

    @pytest.mark.asyncio
    async def test_call_api_passes_sampling_configuration_combination(
        self, mocked_openai_client
    ):
        client, mock_client = mocked_openai_client
        config = {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
        }

        await client.call_api(
            model='gpt-4o-mini',
            instructions='Instr',
            messages=[],
            config=config,
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs == {
            'model': 'gpt-4o-mini',
            'instructions': 'Instr',
            'input': [],
            'temperature': 0.7,
            'top_p': 0.9,
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize('parameter', ['temperature', 'top_p'])
    async def test_call_api_omits_sampling_for_gpt5_models(
        self, mocked_openai_client, parameter
    ):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={parameter: 0.7},
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert parameter not in kwargs

    @pytest.mark.asyncio
    async def test_call_api_omits_sampling_when_gpt52_reasoning_is_enabled(
        self, mocked_openai_client
    ):
        client, mock_client = mocked_openai_client

        await client.call_api(
            model='gpt-5.2',
            instructions='Instr',
            messages=[],
            config={
                'think': 'low',
                'temperature': 0.7,
                'top_p': 0.9,
            },
        )

        kwargs = mock_client.responses.create.call_args.kwargs
        assert kwargs['reasoning'] == {'effort': 'low'}
        assert 'temperature' not in kwargs
        assert 'top_p' not in kwargs

    @pytest.mark.asyncio
    async def test_call_api_passes_tools(self, mocked_openai_client):
        client, mock_client = mocked_openai_client

        tools = [{'type': 'function', 'function': {'name': 'test_tool'}}]

        await client.call_api(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={},
            tools=tools,
        )

        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs['tools'] == tools
