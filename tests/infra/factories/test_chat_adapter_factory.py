from unittest.mock import Mock, patch

import pytest

from createagents.application.interfaces import ChatRepository
from createagents.infra.adapters.Ollama.ollama_chat_adapter import (
    OllamaChatAdapter,
)
from createagents.infra.adapters.OpenAI.openai_chat_adapter import (
    OpenAIChatAdapter,
)
from createagents.infra.factories.chat_adapter_factory import (
    ChatAdapterFactory,
)

OPENAI_CLIENT = (
    'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
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

    @pytest.mark.parametrize('provider', ['invalid', '', 'gpt-5', 'anthropic'])
    def test_unknown_provider_raises_value_error(self, provider):
        with pytest.raises(ValueError, match='Invalid provider'):
            ChatAdapterFactory.create(provider=provider)

    def test_none_provider_raises(self):
        with pytest.raises(AttributeError):
            ChatAdapterFactory.create(provider=None)


@pytest.mark.unit
class TestAdapterIsolation:
    """Adapters own their metrics, so agents must never share one."""

    def test_each_call_returns_a_new_adapter(self):
        first = ChatAdapterFactory.create(provider='ollama')
        second = ChatAdapterFactory.create(provider='ollama')

        assert first is not second

    def test_metrics_do_not_leak_between_adapters(self):
        from createagents.domain import ChatMetrics

        first = ChatAdapterFactory.create(provider='ollama')
        second = ChatAdapterFactory.create(provider='ollama')

        first._OllamaChatAdapter__metrics.append(
            ChatMetrics(model='phi4', latency_ms=1.0, success=True)
        )

        assert len(first.get_metrics()) == 1
        assert second.get_metrics() == []

    def test_openai_adapters_are_also_independent(self, openai_ready):
        first = ChatAdapterFactory.create(provider='openai')
        second = ChatAdapterFactory.create(provider='openai')

        assert first is not second
