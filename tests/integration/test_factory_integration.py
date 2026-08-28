from unittest.mock import Mock, patch

import pytest

from createagents.application import ChatRepository
from createagents.infra import (
    ChatAdapterFactory,
    OllamaChatAdapter,
    OpenAIChatAdapter,
)

# allow-assertion-reduction: Retired shared-cache scenarios were consolidated into fresh-instance and public adapter-port coverage.


@pytest.mark.unit
class TestChatAdapterFactoryUnit:
    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_creates_openai_adapter(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider='openai')
        assert isinstance(adapter, OpenAIChatAdapter)
        assert isinstance(adapter, ChatRepository)

    def test_factory_creates_ollama_adapter(self):
        adapter = ChatAdapterFactory.create(provider='ollama')
        assert isinstance(adapter, OllamaChatAdapter)
        assert isinstance(adapter, ChatRepository)

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_openai_adapter_exposes_chat_port(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_get_client.return_value = Mock()

        adapter = ChatAdapterFactory.create(provider='openai')

        assert callable(adapter.chat)

    def test_factory_ollama_adapter_exposes_chat_port(self):
        adapter = ChatAdapterFactory.create(provider='ollama')

        assert callable(adapter.chat)

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_provider_selection(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter_openai = ChatAdapterFactory.create(provider='openai')
        adapter_ollama = ChatAdapterFactory.create(provider='ollama')

        assert isinstance(adapter_openai, OpenAIChatAdapter)
        assert isinstance(adapter_ollama, OllamaChatAdapter)
        assert not isinstance(adapter_openai, type(adapter_ollama))

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_returns_new_instance_per_call_openai(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter1 = ChatAdapterFactory.create(provider='openai')
        adapter2 = ChatAdapterFactory.create(provider='openai')

        assert adapter1 is not adapter2
        assert isinstance(adapter1, OpenAIChatAdapter)
        assert isinstance(adapter2, OpenAIChatAdapter)

    def test_factory_returns_new_instance_per_call_ollama(self):
        adapter1 = ChatAdapterFactory.create(provider='ollama')
        adapter2 = ChatAdapterFactory.create(provider='ollama')

        assert adapter1 is not adapter2
        assert isinstance(adapter1, OllamaChatAdapter)
        assert isinstance(adapter2, OllamaChatAdapter)

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.openai.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_case_insensitive_provider_detection(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_get_client.return_value = Mock()

        case_variations = ['openai', 'OpenAI', 'OPENAI', 'oPeNaI']
        for provider in case_variations:
            adapter = ChatAdapterFactory.create(provider=provider)
            assert isinstance(adapter, OpenAIChatAdapter)
            assert isinstance(adapter, ChatRepository)

    @pytest.mark.parametrize('provider', ['invalid', '', 'anthropic'])
    def test_factory_rejects_invalid_provider(self, provider):
        with pytest.raises(ValueError, match='Invalid provider'):
            ChatAdapterFactory.create(provider=provider)

    @patch(
        'createagents.infra.adapters.openai.openai_client.EnvironmentConfig.get_api_key'
    )
    def test_factory_handles_missing_api_key(self, mock_get_api_key):
        from createagents.domain.exceptions import ChatException

        mock_get_api_key.side_effect = OSError('API key not found')

        with pytest.raises(ChatException, match='Error configuring OpenAI'):
            ChatAdapterFactory.create(provider='openai')
