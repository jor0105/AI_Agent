from unittest.mock import MagicMock, patch

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter

IA_OLLAMA_TEST_1: str = "phi4-mini:latest"
IA_OLLAMA_TEST_2: str = "gemma3:4b"


@pytest.mark.unit
class TestOllamaChatAdapter:
    """Testes para OllamaChatAdapter."""

    def test_initialization(self):
        adapter = OllamaChatAdapter()

        assert adapter is not None
        assert hasattr(adapter, "_OllamaChatAdapter__logger")
        assert hasattr(adapter, "_OllamaChatAdapter__metrics")
        assert hasattr(adapter, "_OllamaChatAdapter__host")
        assert hasattr(adapter, "_OllamaChatAdapter__max_retries")

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_valid_input(self, mock_chat):
        # Mock correto: response_api é um objeto com atributo message
        mock_response = MagicMock()
        mock_response.message.content = "Ollama response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Be helpful",
            config={},
            history=[],
            user_ask="Hello",
        )

        assert response == "Ollama response"
        mock_chat.assert_called_once()

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_constructs_messages_correctly(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="System instruction",
            config={},
            history=[{"role": "user", "content": "Previous message"}],
            user_ask="User question",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 3
        assert messages[0] == {"role": "system", "content": "System instruction"}
        assert messages[1] == {"role": "user", "content": "Previous message"}
        assert messages[2] == {"role": "user", "content": "User question"}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_history(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Instructions",
            config={},
            history=[],
            user_ask="Question",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 2  # system + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_multiple_history_items(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "Msg 1"},
            {"role": "assistant", "content": "Reply 1"},
            {"role": "user", "content": "Msg 2"},
            {"role": "assistant", "content": "Reply 2"},
        ]

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Instructions",
            config={},
            history=history,
            user_ask="New question",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 6  # system + 4 history + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_correct_model(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs["model"] == IA_OLLAMA_TEST_1

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_response_raises_error(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = ""
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Ollama retornou uma resposta vazia"):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_none_response_raises_error(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = None
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Ollama retornou uma resposta vazia"):
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_missing_message_key_raises_error(self, mock_chat):
        # Cria um objeto customizado que lança AttributeError ao acessar content
        class BadMessage:
            @property
            def content(self):
                raise AttributeError("'dict' object has no attribute 'content'")

        mock_response = MagicMock()
        mock_response.message = BadMessage()
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Erro ao comunicar com Ollama"):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_attribute_error_raises_chat_exception(self, mock_chat):
        # Cria um objeto customizado que lança AttributeError ao acessar message
        class BadResponse:
            @property
            def message(self):
                raise AttributeError("'ChatResponse' object has no attribute 'message'")

        mock_chat.return_value = BadResponse()

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Erro ao comunicar com Ollama"):
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_type_error_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = TypeError("Invalid type")

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Erro de tipo"):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_generic_exception_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = RuntimeError("Connection error")

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="Erro ao comunicar com Ollama"):
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_preserves_original_error(self, mock_chat):
        original_error = RuntimeError("Original error")
        mock_chat.side_effect = original_error

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
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
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

        assert exc_info.value is original_exception

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_special_characters(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = "Resposta com 你好 e emojis 🎉"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test 你好",
            config={},
            history=[],
            user_ask="Question 🎉",
        )

        assert "你好" in response
        assert "🎉" in response

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_multiline_content(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.content = "Line 1\nLine 2\nLine 3"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Multi\nline\ninstructions",
            config={},
            history=[],
            user_ask="Multi\nline\nquestion",
        )

        assert "\n" in response
        assert "Line 1" in response

    def test_adapter_implements_chat_repository_interface(self):
        from src.application.interfaces.chat_repository import ChatRepository

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_collects_metrics_on_success(self, mock_chat):
        """Testa se as métricas são coletadas corretamente em caso de sucesso."""
        mock_response = MagicMock()
        mock_response.message.content = "Success response"
        mock_response.get.return_value = 100  # eval_count
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            history=[],
            user_ask="Test",
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 100
        assert metrics[0].latency_ms > 0

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_collects_metrics_on_failure(self, mock_chat):
        """Testa se as métricas são coletadas corretamente em caso de erro."""
        mock_chat.side_effect = RuntimeError("Test error")

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OLLAMA_TEST_2
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_collects_multiple_metrics(self, mock_chat):
        """Testa se múltiplas métricas são coletadas em várias chamadas."""
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        # Primeira chamada
        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            history=[],
            user_ask="Test 1",
        )

        # Segunda chamada
        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={},
            history=[],
            user_ask="Test 2",
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[1].model == IA_OLLAMA_TEST_2

    def test_get_metrics_returns_copy(self):
        """Testa se get_metrics retorna uma cópia e não a lista original."""
        adapter = OllamaChatAdapter()

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        # Verifica que são listas diferentes
        assert metrics1 is not metrics2

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_string_in_history(self, mock_chat):
        """Testa chat com strings vazias no histórico."""
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Previous response"},
        ]

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            history=history,
            user_ask="New question",
        )

        assert response == "Response"
        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 4  # system + 2 history + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_long_history(self, mock_chat):
        """Testa chat com histórico longo."""
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        # Cria histórico com 50 mensagens
        history = []
        for i in range(25):
            history.append({"role": "user", "content": f"Message {i}"})
            history.append({"role": "assistant", "content": f"Reply {i}"})

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={},
            history=history,
            user_ask="Final question",
        )

        assert response == "Response"
        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 52  # system + 50 history + user

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_config_parameter(self, mock_chat):
        """Testa se o parâmetro config é aceito corretamente."""
        mock_response = MagicMock()
        mock_response.message.content = "Response"
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        config = {"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9}

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config=config,
            history=[],
            user_ask="Test",
        )

        assert response == "Response"

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_key_error_raises_chat_exception(self, mock_chat):
        """Testa se KeyError é tratado corretamente."""
        mock_response = MagicMock()
        # Faz com que acessar .message.content lance KeyError
        type(mock_response.message).content = property(
            lambda self: (_ for _ in ()).throw(KeyError("test_key"))
        )
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="formato inválido.*Chave ausente"):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_metrics_contain_error_message_on_empty_response(self, mock_chat):
        """Testa se a mensagem de erro é registrada nas métricas."""
        mock_response = MagicMock()
        mock_response.message.content = ""
        mock_response.get.return_value = None
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].error_message == "Ollama retornou resposta vazia"
        assert metrics[0].success is False
