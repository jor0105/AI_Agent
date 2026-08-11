from unittest.mock import Mock, patch

import pytest

from createagents.application import ChatRepository
from createagents.infra import (
    ChatAdapterFactory,
    OllamaChatAdapter,
    OpenAIChatAdapter,
)


@pytest.mark.integration
class TestChatAdapterFactoryIntegration:
    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_creates_openai_adapter_for_gpt_models(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        gpt_models = ['gpt-4.1-mini', 'gpt-5-mini', 'gpt-5-nano', 'GPT-5-NANO']

        for model in gpt_models:
            adapter = ChatAdapterFactory.create(provider='openai', model=model)
            assert isinstance(adapter, OpenAIChatAdapter)
            assert isinstance(adapter, ChatRepository)

    def test_factory_creates_ollama_adapter_for_non_gpt_models(self):
        non_gpt_models = [
            'gemma3:4b',
            'granite4:latest',
            'llama2',
            'mistral',
            'claude',
            'random-model',
        ]

        for model in non_gpt_models:
            adapter = ChatAdapterFactory.create(provider='ollama', model=model)
            assert isinstance(adapter, OllamaChatAdapter)
            assert isinstance(adapter, ChatRepository)

    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_provider_selection(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter_openai = ChatAdapterFactory.create(
            provider='openai', model='any-model'
        )
        adapter_ollama = ChatAdapterFactory.create(
            provider='ollama', model='any-model'
        )
        assert not isinstance(adapter_openai, type(adapter_ollama))

    def test_factory_adapter_has_chat_method_openai(self):
        with patch(
            'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
        ) as mock_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
            ) as mock_client:
                mock_key.return_value = 'test-key'
                mock_client.return_value = Mock()

                ChatAdapterFactory.clear_cache()

                adapter = ChatAdapterFactory.create(
                    provider='openai', model='gpt-5-mini'
                )

                assert hasattr(adapter, 'chat')
                assert callable(adapter.chat)

    def test_factory_adapter_has_chat_method_ollama(self):
        adapter = ChatAdapterFactory.create(
            provider='ollama', model='gemma3:4b'
        )

        assert hasattr(adapter, 'chat')
        assert callable(adapter.chat)

    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_uses_cache_for_same_model(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider='openai', model='gpt-5')
        adapter2 = ChatAdapterFactory.create(provider='openai', model='gpt-5')

        assert adapter1 is adapter2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
    )
    def test_factory_creates_different_adapters_for_different_models(
        self, mock_get_client, mock_get_api_key
    ):
        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = 'test-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(
            provider='openai', model='gpt-5-mini'
        )
        adapter2 = ChatAdapterFactory.create(
            provider='openai', model='gemma3:4b'
        )

        assert adapter1 is not adapter2

    def test_factory_case_insensitive_gpt_detection(self):
        with patch(
            'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
        ) as mock_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
            ) as mock_client:
                mock_key.return_value = 'test-key'
                mock_client.return_value = Mock()

                ChatAdapterFactory.clear_cache()

                case_variations = [
                    'gpt-5',
                    'GPT-5',
                    'Gpt-5-mini',
                    'GPT-5-NANO',
                    'gpt-5-nano',
                ]

                for model in case_variations:
                    adapter = ChatAdapterFactory.create(
                        provider='openai', model=model
                    )
                    assert isinstance(adapter, OpenAIChatAdapter)

    def test_factory_ollama_adapter_has_metrics(self):
        adapter = ChatAdapterFactory.create(
            provider='ollama', model='gemma3:4b'
        )
        assert hasattr(adapter, 'get_metrics')

    def test_factory_openai_adapter_has_metrics(self):
        with patch(
            'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
        ) as mock_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
            ) as mock_client:
                mock_key.return_value = 'test-key'
                mock_client.return_value = Mock()

                adapter = ChatAdapterFactory.create(
                    provider='openai', model='gpt-5-nano'
                )
                assert hasattr(adapter, 'get_metrics')

    def test_factory_returns_chat_repository_interface(self):
        test_cases = [
            ('openai', 'gpt-5-mini'),
            ('ollama', 'gemma3:4b'),
            ('openai', 'gpt-5-nano'),
            ('ollama', 'phi4-mini:latest'),
        ]

        with patch(
            'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
        ) as mock_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
            ) as mock_client:
                mock_key.return_value = 'test-key'
                mock_client.return_value = Mock()

                for provider, model in test_cases:
                    adapter = ChatAdapterFactory.create(
                        provider=provider, model=model
                    )
                    assert isinstance(adapter, ChatRepository)
                    assert hasattr(adapter, 'chat')
                    assert callable(adapter.chat)

    @patch(
        'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
    )
    def test_factory_handles_missing_api_key(self, mock_get_api_key):
        from createagents.domain.exceptions import ChatException

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.side_effect = OSError('API key not found')

        with pytest.raises(ChatException, match='Error configuring OpenAI'):
            ChatAdapterFactory.create(provider='openai', model='gpt-5-mini')

    def test_factory_logic_consistency(self):
        ollama_models = [
            'gemma3:4b',
            'phi4-mini:latest',
            'llama2',
            'any-model',
        ]
        for model in ollama_models:
            adapter = ChatAdapterFactory.create(provider='ollama', model=model)
            assert isinstance(adapter, OllamaChatAdapter), (
                f'Model {model} with ollama provider should use OllamaChatAdapter'
            )

        with patch(
            'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
        ) as mock_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
            ) as mock_client:
                mock_key.return_value = 'test-key'
                mock_client.return_value = Mock()

                openai_models = [
                    'gpt-5-mini',
                    'gpt-5-nano',
                    'gpt-4',
                    'any-model',
                ]
                for model in openai_models:
                    adapter = ChatAdapterFactory.create(
                        provider='openai', model=model
                    )
                    assert isinstance(adapter, OpenAIChatAdapter), (
                        f'Model {model} with openai provider should use OpenAIChatAdapter'
                    )

    def test_factory_clear_cache_works(self):
        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(
            provider='ollama', model='gemma3:4b'
        )

        ChatAdapterFactory.clear_cache()

        adapter2 = ChatAdapterFactory.create(
            provider='ollama', model='gemma3:4b'
        )

        assert adapter1 is not adapter2

    def test_factory_cache_key_includes_provider(self):
        with patch(
            'createagents.infra.adapters.OpenAI.openai_client.EnvironmentConfig.get_api_key'
        ) as mock_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_client.ClientOpenAI.get_client'
            ) as mock_client:
                mock_key.return_value = 'test-key'
                mock_client.return_value = Mock()

                ChatAdapterFactory.clear_cache()

                adapter_openai = ChatAdapterFactory.create(
                    provider='openai', model='any-model'
                )
                adapter_ollama = ChatAdapterFactory.create(
                    provider='ollama', model='any-model'
                )

                assert adapter_openai is not adapter_ollama
                assert not isinstance(adapter_openai, type(adapter_ollama))
