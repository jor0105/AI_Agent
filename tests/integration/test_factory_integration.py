from unittest.mock import Mock, patch

import pytest

from src.application.interfaces.chat_repository import ChatRepository
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory


@pytest.mark.integration
class TestChatAdapterFactoryIntegration:
    """Testes de integração para ChatAdapterFactory."""

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_factory_creates_openai_adapter_for_gpt_models(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        gpt_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano", "GPT-5-NANO"]

        for model in gpt_models:
            adapter = ChatAdapterFactory.create(provider="openai", model=model)
            assert isinstance(adapter, OpenAIChatAdapter)
            assert isinstance(adapter, ChatRepository)

    def test_factory_creates_ollama_adapter_for_non_gpt_models(self):
        non_gpt_models = [
            "gemma3:4b",
            "phi4-mini:latest",
            "llama2",
            "mistral",
            "claude",
            "random-model",
        ]

        for model in non_gpt_models:
            adapter = ChatAdapterFactory.create(provider="ollama", model=model)
            assert isinstance(adapter, OllamaChatAdapter)
            assert isinstance(adapter, ChatRepository)

    def test_factory_provider_selection(self):
        """Testa que factory respeita o parâmetro provider."""
        # OpenAI provider
        adapter_openai = ChatAdapterFactory.create(provider="openai", model="any-model")
        # Ollama provider
        adapter_ollama = ChatAdapterFactory.create(provider="ollama", model="any-model")

        # Tipos diferentes baseados no provider
        assert type(adapter_openai) != type(adapter_ollama)

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_factory_adapter_can_chat_openai(
        self, mock_ollama, mock_get_client, mock_get_api_key
    ):
        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-key"
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "OpenAI response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        response = adapter.chat(
            model="gpt-5-mini", instructions="Be helpful", user_ask="Hello", history=[]
        )

        assert response == "OpenAI response"
        assert mock_client.chat.completions.create.called

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_factory_adapter_can_chat_ollama(self, mock_ollama_chat):
        mock_ollama_chat.return_value = {"message": {"content": "Ollama response"}}

        adapter = ChatAdapterFactory.create(provider="ollama", model="gemma3:4b")

        response = adapter.chat(
            model="gemma3:4b", instructions="Be helpful", user_ask="Hello", history=[]
        )

        assert response == "Ollama response"
        assert mock_ollama_chat.called

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_factory_uses_cache_for_same_model(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert adapter1 is adapter2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_factory_creates_different_adapters_for_different_models(
        self, mock_get_client, mock_get_api_key
    ):
        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gemma3:4b")

        assert adapter1 is not adapter2

    def test_factory_case_insensitive_gpt_detection(self):
        with patch(
            "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
        ) as mock_key:
            with patch(
                "src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
            ) as mock_client:
                mock_key.return_value = "test-key"
                mock_client.return_value = Mock()

                ChatAdapterFactory.clear_cache()

                case_variations = [
                    "gpt-5",
                    "GPT-5",
                    "Gpt-5-mini",
                    "GPT-5-NANO",
                    "gpt-5-nano",
                ]

                for model in case_variations:
                    adapter = ChatAdapterFactory.create(provider="openai", model=model)
                    assert isinstance(adapter, OpenAIChatAdapter)

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_factory_adapter_handles_history(
        self, mock_ollama, mock_get_client, mock_get_api_key
    ):
        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-key"
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Response with history"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5-nano")

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        response = adapter.chat(
            model="gpt-5-nano",
            instructions="System prompt",
            user_ask="New question",
            history=history,
        )

        assert response == "Response with history"

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) >= 3  # system + history + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_factory_with_ollama_and_different_models(self, mock_ollama_chat):
        mock_ollama_chat.return_value = {"message": {"content": "Local response"}}

        models = ["gemma3:4b", "phi4-mini:latest", "llama2"]

        for model in models:
            adapter = ChatAdapterFactory.create(provider="ollama", model=model)
            assert isinstance(adapter, OllamaChatAdapter)

            response = adapter.chat(
                model=model, instructions="Test", user_ask="Test", history=[]
            )

            assert response == "Local response"

    def test_factory_returns_chat_repository_interface(self):
        """Testa que factory retorna interface ChatRepository para todos os providers."""
        test_cases = [
            ("openai", "gpt-5-mini"),
            ("ollama", "gemma3:4b"),
            ("openai", "gpt-5-nano"),
            ("ollama", "phi4-mini:latest"),
        ]

        with patch(
            "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
        ) as mock_key:
            with patch(
                "src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
            ) as mock_client:
                mock_key.return_value = "test-key"
                mock_client.return_value = Mock()

                for provider, model in test_cases:
                    adapter = ChatAdapterFactory.create(provider=provider, model=model)
                    assert isinstance(adapter, ChatRepository)
                    assert hasattr(adapter, "chat")
                    assert callable(adapter.chat)

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    def test_factory_handles_missing_api_key(self, mock_get_api_key):
        from src.domain.exceptions import ChatException

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.side_effect = EnvironmentError("API key not found")

        with pytest.raises(ChatException, match="Erro ao configurar OpenAI"):
            ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

    def test_factory_logic_consistency(self):
        """Testa consistência na escolha de adapters baseado no provider."""
        # Testa Ollama provider
        ollama_models = ["gemma3:4b", "phi4-mini:latest", "llama2", "any-model"]
        for model in ollama_models:
            adapter = ChatAdapterFactory.create(provider="ollama", model=model)
            assert isinstance(
                adapter, OllamaChatAdapter
            ), f"Model {model} with ollama provider should use OllamaChatAdapter"

        # Testa OpenAI provider
        with patch(
            "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
        ) as mock_key:
            with patch(
                "src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
            ) as mock_client:
                mock_key.return_value = "test-key"
                mock_client.return_value = Mock()

                openai_models = ["gpt-5-mini", "gpt-5-nano", "gpt-4", "any-model"]
                for model in openai_models:
                    adapter = ChatAdapterFactory.create(provider="openai", model=model)
                    assert isinstance(
                        adapter, OpenAIChatAdapter
                    ), f"Model {model} with openai provider should use OpenAIChatAdapter"
