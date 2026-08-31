from typing import cast
from unittest.mock import Mock, patch

import pytest

from createagents.application.interfaces import ChatRepository
from createagents.infra.adapters.ollama.ollama_chat_adapter import (
    OllamaChatAdapter,
)
from createagents.infra.adapters.openai.openai_chat_adapter import (
    OpenAIChatAdapter,
)
from createagents.infra.factories.chat_adapter_factory import (
    ChatAdapterFactory,
)
from tests.test_constants import OLLAMA_MODEL_PHI

OPENAI_CLIENT = (
    'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
)

# allow-assertion-reduction: Removed cache and model-key cases target the retired shared-adapter cache; isolation coverage remains below.


@pytest.fixture
def openai_ready():
    """Stub the credentials and SDK client the OpenAI adapter needs."""
    with (
        patch(
            'createagents.infra.config.EnvironmentConfig.get_api_key',
            return_value='test-api-key',
        ),
        patch(OPENAI_CLIENT, return_value=Mock()),
    ):
        yield


@pytest.mark.unit
class TestChatAdapterFactory:
    def test_creates_openai_adapter(self, openai_ready):
        adapter = ChatAdapterFactory.create(provider='openai')

        assert isinstance(adapter, OpenAIChatAdapter)

    def test_creates_ollama_adapter(self):
        adapter = ChatAdapterFactory.create(provider='ollama')

        assert isinstance(adapter, OllamaChatAdapter)

    def test_created_adapter_implements_the_port(self):
        adapter = ChatAdapterFactory.create(provider='ollama')

        assert isinstance(adapter, ChatRepository)

    def test_ollama_does_not_require_an_api_key(self):
        with patch(
            'createagents.infra.config.EnvironmentConfig.get_api_key',
            side_effect=AssertionError('Ollama must not read an API key'),
        ):
            adapter = ChatAdapterFactory.create(provider='ollama')

        assert isinstance(adapter, OllamaChatAdapter)

    @pytest.mark.parametrize(
        'provider', ['OpenAI', 'OPENAI', 'openai', 'oPeNaI']
    )
    def test_provider_matching_is_case_insensitive(
        self, provider, openai_ready
    ):
        adapter = ChatAdapterFactory.create(provider=provider)

        assert isinstance(adapter, OpenAIChatAdapter)

    @pytest.mark.parametrize(
        'provider', ['invalid', '', 'invalid-provider-model', 'anthropic']
    )
    def test_unknown_provider_raises_value_error(self, provider):
        with pytest.raises(ValueError, match='Invalid provider'):
            ChatAdapterFactory.create(provider=provider)

    def test_none_provider_raises(self):
        with pytest.raises(AttributeError):
            ChatAdapterFactory.create(provider=cast(str, None))


@pytest.mark.unit
class TestAdapterIsolation:
    """Adapters own their metrics, so agents must never share one."""

    def test_each_call_returns_a_new_adapter(self):
        first = ChatAdapterFactory.create(provider='ollama')
        second = ChatAdapterFactory.create(provider='ollama')

        assert first is not second

    @pytest.mark.asyncio
    async def test_metrics_do_not_leak_between_adapters(self):
        first = ChatAdapterFactory.create(provider='ollama')
        second = ChatAdapterFactory.create(provider='ollama')

        assert first.get_metrics() == []
        assert second.get_metrics() == []

        from unittest.mock import AsyncMock, MagicMock

        mock_response = MagicMock()
        mock_response.message = MagicMock(content='Hello', tool_calls=None)
        mock_response.get.side_effect = lambda key, default=None: {
            'prompt_eval_count': 10,
            'eval_count': 20,
            'total_duration': 100_000_000,
        }.get(key, default)

        with patch(
            'createagents.infra.adapters.ollama.ollama_client.OllamaClient.call_api',
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await first.chat(
                model=OLLAMA_MODEL_PHI,
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Hi',
            )
            assert response == 'Hello'

        first_metrics = first.get_metrics()
        second_metrics = second.get_metrics()

        assert len(first_metrics) == 1
        assert first_metrics[0].model == OLLAMA_MODEL_PHI
        assert first_metrics[0].prompt_tokens == 10
        assert first_metrics[0].completion_tokens == 20
        assert first_metrics[0].success is True

        assert len(second_metrics) == 0

        first_metrics.clear()
        assert len(first.get_metrics()) == 1

    def test_openai_adapters_are_also_independent(self, openai_ready):
        first = ChatAdapterFactory.create(provider='openai')
        second = ChatAdapterFactory.create(provider='openai')

        assert first is not second
