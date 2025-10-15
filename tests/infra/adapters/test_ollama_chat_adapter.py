from unittest.mock import patch

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter


@pytest.mark.unit
class TestOllamaChatAdapter:
    """Testes para OllamaChatAdapter."""

    def test_initialization(self):
        adapter = OllamaChatAdapter()

        assert adapter is not None

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_valid_input(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "Ollama response"}}

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model="gemma3:4b",
            instructions="Be helpful",
            user_ask="Hello",
            history=[],
        )

        assert response == "Ollama response"
        mock_chat.assert_called_once()

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_constructs_messages_correctly(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "Response"}}

        adapter = OllamaChatAdapter()

        adapter.chat(
            model="phi4-mini:latest",
            instructions="System instruction",
            user_ask="User question",
            history=[{"role": "user", "content": "Previous message"}],
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 3
        assert messages[0] == {"role": "system", "content": "System instruction"}
        assert messages[1] == {"role": "user", "content": "Previous message"}
        assert messages[2] == {"role": "user", "content": "User question"}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_history(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "Response"}}

        adapter = OllamaChatAdapter()

        adapter.chat(
            model="gemma3:4b",
            instructions="Instructions",
            user_ask="Question",
            history=[],
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 2  # system + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_multiple_history_items(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "Response"}}

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "Msg 1"},
            {"role": "assistant", "content": "Reply 1"},
            {"role": "user", "content": "Msg 2"},
            {"role": "assistant", "content": "Reply 2"},
        ]

        adapter.chat(
            model="phi4-mini:latest",
            instructions="Instructions",
            user_ask="New question",
            history=history,
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 6  # system + 4 history + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_correct_model(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "Response"}}

        adapter = OllamaChatAdapter()

        adapter.chat(
            model="phi4-mini:latest",
            instructions="Test",
            user_ask="Test",
            history=[],
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs["model"] == "phi4-mini:latest"

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_response_raises_error(self, mock_chat):
        mock_chat.return_value = {"message": {"content": ""}}

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Ollama retornou uma resposta vazia"):
            adapter.chat(
                model="gemma3:4b",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_none_response_raises_error(self, mock_chat):
        mock_chat.return_value = {"message": {"content": None}}

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Ollama retornou uma resposta vazia"):
            adapter.chat(
                model="phi4-mini:latest",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_missing_message_key_raises_error(self, mock_chat):
        mock_chat.return_value = {"wrong_key": "value"}

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="formato inválido.*Chave ausente"):
            adapter.chat(
                model="gemma3:4b",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_missing_content_key_raises_error(self, mock_chat):
        mock_chat.return_value = {"message": {"wrong_key": "value"}}

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="formato inválido.*Chave ausente"):
            adapter.chat(
                model="phi4-mini:latest",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_type_error_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = TypeError("Invalid type")

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Erro de tipo"):
            adapter.chat(
                model="gemma3:4b",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_generic_exception_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = RuntimeError("Connection error")

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Erro ao comunicar com Ollama"):
            adapter.chat(
                model="phi4-mini:latest",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_preserves_original_error(self, mock_chat):
        original_error = RuntimeError("Original error")
        mock_chat.side_effect = original_error

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model="gemma3:4b",
                instructions="Test",
                user_ask="Test",
                history=[],
            )
        except ChatException as e:
            assert e.original_error is original_error

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_propagates_chat_exception(self, mock_chat):
        original_exception = ChatException("Original chat error")
        mock_chat.side_effect = original_exception

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException) as exc_info:
            adapter.chat(
                model="phi4-mini:latest",
                instructions="Test",
                user_ask="Test",
                history=[],
            )

        assert exc_info.value is original_exception

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_special_characters(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": "Resposta com 你好 e emojis 🎉"}
        }

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model="phi4-mini:latest",
            instructions="Test 你好",
            user_ask="Question 🎉",
            history=[],
        )

        assert "你好" in response
        assert "🎉" in response

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_multiline_content(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "Line 1\nLine 2\nLine 3"}}

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model="gemma3:4b",
            instructions="Multi\nline\ninstructions",
            user_ask="Multi\nline\nquestion",
            history=[],
        )

        assert "\n" in response
        assert "Line 1" in response

    def test_adapter_implements_chat_repository_interface(self):
        from src.application.interfaces.chat_repository import ChatRepository

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)
