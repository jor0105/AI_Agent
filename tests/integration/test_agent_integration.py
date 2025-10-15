from unittest.mock import Mock, patch

import pytest

from src.domain.exceptions import ChatException, InvalidAgentConfigException
from src.presentation.agent_controller import AIAgent


@pytest.mark.integration
class TestAgentIntegration:
    """Testes de integração para o fluxo completo do agente."""

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_create_agent_and_chat_with_openai(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Hello! How can I help you?"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = AIAgent(
            provider="openai",
            model="gpt-5-mini",
            name="Assistant",
            instructions="You are a helpful assistant",
        )

        response = agent.chat("Hello")

        assert response == "Hello! How can I help you?"
        assert mock_client.chat.completions.create.called

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_create_agent_and_chat_with_ollama(self, mock_ollama_chat):
        mock_ollama_chat.return_value = {
            "message": {"content": "Hi there! I'm here to help."}
        }

        agent = AIAgent(
            provider="ollama",
            model="gemma3:4b",
            name="Local Assistant",
            instructions="You are a helpful local AI",
        )

        response = agent.chat("Hi")

        assert response == "Hi there! I'm here to help."
        assert mock_ollama_chat.called

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_conversation_flow_with_history(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()

        responses = [
            "Nice to meet you!",
            "I'm doing great, thanks!",
            "Sure, I can help with that.",
        ]

        def create_mock_response(content):
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = content
            mock_choice = Mock()
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_client.chat.completions.create.side_effect = [
            create_mock_response(r) for r in responses
        ]
        mock_get_client.return_value = mock_client

        agent = AIAgent(
            provider="openai",
            model="gpt-5-nano",
            name="Chatbot",
            instructions="You are friendly",
        )

        r1 = agent.chat("Hello, my name is John")
        r2 = agent.chat("How are you?")
        r3 = agent.chat("Can you help me?")

        assert r1 == "Nice to meet you!"
        assert r2 == "I'm doing great, thanks!"
        assert r3 == "Sure, I can help with that."

        configs = agent.get_configs()
        assert len(configs["history"]) == 6

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_clear_history_integration(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()

        def create_mock_response(content):
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = content
            mock_choice = Mock()
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_client.chat.completions.create.side_effect = [
            create_mock_response("Response 1"),
            create_mock_response("Response 2"),
        ]
        mock_get_client.return_value = mock_client

        agent = AIAgent(
            provider="openai",
            model="gpt-5-nano",
            name="Agent",
            instructions="Be helpful",
        )

        agent.chat("Message 1")
        assert len(agent.get_configs()["history"]) == 2

        agent.clear_history()
        assert len(agent.get_configs()["history"]) == 0

        agent.chat("Message 2")
        assert len(agent.get_configs()["history"]) == 2

    def test_invalid_agent_creation_fails(self):
        with pytest.raises(InvalidAgentConfigException):
            AIAgent(provider="openai", model="", name="Test", instructions="Test")

        with pytest.raises(InvalidAgentConfigException):
            AIAgent(provider="openai", model="gpt-5-mini", name="", instructions="Test")

        with pytest.raises(InvalidAgentConfigException):
            AIAgent(provider="openai", model="gpt-5-mini", name="Test", instructions="")

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_error_handling(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API Error")
        mock_get_client.return_value = mock_client

        agent = AIAgent(
            provider="openai", model="gpt-5-nano", name="Agent", instructions="Test"
        )

        with pytest.raises(ChatException):
            agent.chat("Hello")

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_history_not_updated_on_error(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()

        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Success"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_client.chat.completions.create.side_effect = [
            mock_response,
            RuntimeError("API Error"),
        ]
        mock_get_client.return_value = mock_client

        agent = AIAgent(
            provider="openai", model="gpt-5-mini", name="Agent", instructions="Test"
        )

        agent.chat("Message 1")
        assert len(agent.get_configs()["history"]) == 2

        with pytest.raises(ChatException):
            agent.chat("Message 2")

        assert len(agent.get_configs()["history"]) == 2

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_get_configs_returns_complete_info(self, mock_ollama_chat):
        mock_ollama_chat.return_value = {"message": {"content": "Response"}}

        agent = AIAgent(
            provider="ollama",
            model="phi4-mini:latest",
            name="TestAgent",
            instructions="Test instructions",
        )

        agent.chat("Test")

        configs = agent.get_configs()

        assert "name" in configs
        assert "model" in configs
        assert "instructions" in configs
        assert "history" in configs
        assert "provider" in configs
        assert configs["name"] == "TestAgent"
        assert configs["model"] == "phi4-mini:latest"
        assert configs["instructions"] == "Test instructions"
        assert configs["provider"] == "ollama"
        assert len(configs["history"]) == 2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_multiple_agents_are_independent(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()

        def create_mock_response(content):
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = content
            mock_choice = Mock()
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_client.chat.completions.create.side_effect = [
            create_mock_response("Response A1"),
            create_mock_response("Response B1"),
            create_mock_response("Response A2"),
        ]
        mock_get_client.return_value = mock_client

        agent_a = AIAgent(
            provider="openai",
            model="gpt-5-mini",
            name="Agent A",
            instructions="You are A",
        )

        agent_b = AIAgent(
            provider="openai",
            model="gpt-5-nano",
            name="Agent B",
            instructions="You are B",
        )

        agent_a.chat("Message to A")
        agent_b.chat("Message to B")
        agent_a.chat("Another to A")

        config_a = agent_a.get_configs()
        config_b = agent_b.get_configs()

        assert len(config_a["history"]) == 4
        assert len(config_b["history"]) == 2
        assert config_a["name"] == "Agent A"
        assert config_b["name"] == "Agent B"

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_empty_message_validation(self, mock_get_client, mock_get_api_key):
        from src.infra.factories.chat_adapter_factory import ChatAdapterFactory

        ChatAdapterFactory.clear_cache()

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        agent = AIAgent(
            provider="openai", model="gpt-5-nano", name="Agent", instructions="Test"
        )

        with pytest.raises(ValueError, match="mensagem não pode estar vazia"):
            agent.chat("")

        with pytest.raises(ValueError, match="mensagem não pode estar vazia"):
            agent.chat("   ")
