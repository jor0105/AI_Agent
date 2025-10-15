from unittest.mock import Mock, patch

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter


@pytest.mark.unit
class TestOpenAIChatAdapter:
    """Testes para OpenAIChatAdapter."""

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_initialization_success(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        assert adapter is not None
        mock_get_api_key.assert_called_once_with("OPENAI_API_KEY")
        mock_get_client.assert_called_once_with("test-api-key")

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    def test_initialization_with_missing_api_key_raises_error(self, mock_get_api_key):
        mock_get_api_key.side_effect = EnvironmentError("API key not found")

        with pytest.raises(ChatException, match="Erro ao configurar OpenAI"):
            OpenAIChatAdapter()

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_valid_input(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "OpenAI response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model="gpt-5-mini",
            instructions="Be helpful",
            user_ask="Hello",
            history=[],
        )

        assert response == "OpenAI response"
        mock_client.chat.completions.create.assert_called_once()

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_constructs_messages_correctly(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model="gpt-5-nano",
            instructions="System instruction",
            user_ask="User question",
            history=[{"role": "user", "content": "Previous message"}],
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 3
        assert messages[0] == {"role": "system", "content": "System instruction"}
        assert messages[1] == {"role": "user", "content": "Previous message"}
        assert messages[2] == {"role": "user", "content": "User question"}

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_empty_history(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model="gpt-5-nano",
            instructions="Instructions",
            user_ask="Question",
            history=[],
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_multiple_history_items(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        history = [
            {"role": "user", "content": "Msg 1"},
            {"role": "assistant", "content": "Reply 1"},
            {"role": "user", "content": "Msg 2"},
            {"role": "assistant", "content": "Reply 2"},
        ]

        adapter.chat(
            model="gpt-5-mini",
            instructions="Instructions",
            user_ask="New question",
            history=history,
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 6

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_passes_correct_model(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Response"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model="gpt-5-nano",
            instructions="Test",
            user_ask="Test",
            history=[],
        )

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-5-nano"

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_empty_response_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = ""
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException, match="OpenAI retornou uma resposta vazia"):
            adapter.chat(
                model="gpt-5-nano",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_none_response_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = None
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException, match="OpenAI retornou uma resposta vazia"):
            adapter.chat(
                model="gpt-5-mini",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_missing_choices_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException, match="formato inesperado"):
            adapter.chat(
                model="gpt-5-nano",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_attribute_error_raises_chat_exception(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = AttributeError(
            "Missing attribute"
        )
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException, match="Erro ao acessar resposta da OpenAI"):
            adapter.chat(
                model="gpt-5-nano",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_generic_exception_raises_chat_exception(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API error")
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException, match="Erro ao comunicar com OpenAI"):
            adapter.chat(
                model="gpt-5-mini",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_preserves_original_error(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        original_error = RuntimeError("Original error")
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = original_error
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        try:
            adapter.chat(
                model="gpt-5-nano",
                instructions="Test",
                user_ask="Test",
                history=[],
            )
        except ChatException as e:
            assert e.original_error is original_error

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_propagates_chat_exception(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        original_exception = ChatException("Original chat error")
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = original_exception
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException) as exc_info:
            adapter.chat(
                model="gpt-5-nano",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

        assert exc_info.value is original_exception

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_special_characters(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Resposta com 你好 e emojis 🎉"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model="gpt-5-nano",
            instructions="Test 你好",
            user_ask="Question 🎉",
            history=[],
        )

        assert "你好" in response
        assert "🎉" in response

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_chat_with_multiline_content(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"

        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "Line 1\nLine 2\nLine 3"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model="gpt-5-nano",
            instructions="Multi\nline\ninstructions",
            user_ask="Multi\nline\nquestion",
            history=[],
        )

        assert "\n" in response
        assert "Line 1" in response

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_adapter_implements_chat_repository_interface(
        self, mock_get_client, mock_get_api_key
    ):
        from src.application.interfaces.chat_repository import ChatRepository

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        assert isinstance(adapter, ChatRepository)
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)
