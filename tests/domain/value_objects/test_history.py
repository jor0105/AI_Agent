import pytest

from src.domain.value_objects.history import History
from src.domain.value_objects.message import Message, MessageRole


@pytest.mark.unit
class TestHistory:
    def test_create_empty_history(self):
        history = History()

        assert len(history) == 0
        assert bool(history) is False
        assert history.get_messages() == []

    def test_history_default_max_size(self):
        history = History()
        assert history.max_size == 10

    def test_create_history_with_custom_max_size(self):
        history = History(max_size=5)

        assert history.max_size == 5

    def test_add_message_object(self):
        history = History()
        message = Message(role=MessageRole.USER, content="Hello")

        history.add(message)

        assert len(history) == 1
        assert history.get_messages()[0] == message

    def test_add_invalid_type_raises_error(self):
        history = History()

        with pytest.raises(
            TypeError, match="Apenas objetos do tipo Message podem ser adicionados"
        ):
            history.add("Not a message")

    def test_add_user_message(self):
        history = History()

        history.add_user_message("User message")

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "User message"

    def test_add_assistant_message(self):
        history = History()

        history.add_assistant_message("Assistant response")

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == "Assistant response"

    def test_add_system_message(self):
        history = History()

        history.add_system_message("System instruction")

        assert len(history) == 1
        messages = history.get_messages()
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "System instruction"

    def test_add_multiple_messages(self):
        history = History()

        history.add_user_message("Message 1")
        history.add_assistant_message("Response 1")
        history.add_user_message("Message 2")
        history.add_assistant_message("Response 2")

        assert len(history) == 4

    def test_clear_history(self):
        history = History()
        history.add_user_message("Message 1")
        history.add_user_message("Message 2")

        assert len(history) == 2

        history.clear()

        assert len(history) == 0
        assert bool(history) is False

    def test_get_messages_returns_copy(self):
        history = History()
        history.add_user_message("Test")

        messages1 = history.get_messages()
        messages2 = history.get_messages()

        assert messages1 == messages2
        assert messages1 is not messages2  # Objetos diferentes

    def test_to_dict_list_empty(self):
        history = History()

        result = history.to_dict_list()

        assert result == []
        assert isinstance(result, list)

    def test_to_dict_list_with_messages(self):
        history = History()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi there!")

        result = history.to_dict_list()

        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "Hello"}
        assert result[1] == {"role": "assistant", "content": "Hi there!"}

    def test_from_dict_list_empty(self):
        data = []
        history = History.from_dict_list(data, max_size=5)

        assert len(history) == 0

    def test_from_dict_list_with_messages(self):
        data = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        history = History.from_dict_list(data, max_size=5)

        assert len(history) == 2
        messages = history.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hi!"

    def test_from_dict_list_with_custom_max_size(self):
        data = [{"role": "user", "content": "Test"}]
        history = History().from_dict_list(data, max_size=5)

        assert history.max_size == 5

    def test_history_max_size_limit(self):
        history = History(max_size=3)

        history.add_user_message("Msg 1")
        history.add_user_message("Msg 2")
        history.add_user_message("Msg 3")
        history.add_user_message("Msg 4")
        history.add_user_message("Msg 5")

        assert len(history) == 3
        messages = history.get_messages()
        assert messages[0].content == "Msg 3"
        assert messages[1].content == "Msg 4"
        assert messages[2].content == "Msg 5"

    def test_history_invalid_max_size_raises(self):
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size=None)
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size=0)
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size=-1)

    def test_history_trim_keeps_most_recent(self):
        history = History(max_size=10)

        # Adiciona 15 mensagens
        for i in range(15):
            history.add_user_message(f"Message {i}")

        assert len(history) == 10
        messages = history.get_messages()
        assert messages[0].content == "Message 5"
        assert messages[-1].content == "Message 14"

    def test_history_bool_true_when_has_messages(self):
        history = History()
        history.add_user_message("Test")

        assert bool(history) is True

    def test_history_bool_false_when_empty(self):
        history = History()

        assert bool(history) is False

    def test_history_len_returns_correct_count(self):
        history = History()

        assert len(history) == 0

        history.add_user_message("Msg 1")
        assert len(history) == 1

        history.add_assistant_message("Msg 2")
        assert len(history) == 2

        history.clear()
        assert len(history) == 0

    def test_to_dict_list_and_from_dict_list_roundtrip(self):
        original = History(max_size=10)
        original.add_user_message("User msg")
        original.add_assistant_message("Assistant msg")
        original.add_system_message("System msg")

        dict_list = original.to_dict_list()
        reconstructed = History.from_dict_list(dict_list, max_size=10)

        assert len(original) == len(reconstructed)
        original_messages = original.get_messages()
        reconstructed_messages = reconstructed.get_messages()

        for orig, recon in zip(original_messages, reconstructed_messages):
            assert orig == recon

    def test_history_with_alternating_messages(self):
        history = History(max_size=20)

        for i in range(5):
            history.add_user_message(f"User {i}")
            history.add_assistant_message(f"Assistant {i}")

        assert len(history) == 10
        messages = history.get_messages()

        # Verifica alternância
        for i in range(0, 10, 2):
            assert messages[i].role == MessageRole.USER
            assert messages[i + 1].role == MessageRole.ASSISTANT

    def test_history_preserves_message_order(self):
        history = History()

        history.add_user_message("First")
        history.add_assistant_message("Second")
        history.add_user_message("Third")

        messages = history.get_messages()

        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"

    def test_history_with_special_characters(self):
        history = History(max_size=1)
        special_content = "Hello! 你好 🎉 @#$%"

        history.add_user_message(special_content)

        messages = history.get_messages()
        assert messages[0].content == special_content

    def test_history_with_multiline_content(self):
        history = History()
        multiline = "Line 1\nLine 2\nLine 3"

        history.add_user_message(multiline)

        messages = history.get_messages()
        assert messages[0].content == multiline


@pytest.mark.unit
class TestHistoryDequePerformance:
    def test_history_uses_deque_internally(self):
        from collections import deque

        history = History(max_size=5)
        assert isinstance(history._messages, deque)

    def test_deque_maxlen_is_set_correctly(self):
        history = History(max_size=5)
        assert history._messages.maxlen == 5

    def test_deque_auto_removes_old_messages(self):
        history = History(max_size=3)

        history.add_user_message("Msg 1")
        history.add_user_message("Msg 2")
        history.add_user_message("Msg 3")
        history.add_user_message("Msg 4")  # Deve remover "Msg 1"
        messages = history.get_messages()
        assert len(messages) == 3
        assert messages[0].content == "Msg 2"
        assert messages[1].content == "Msg 3"
        assert messages[2].content == "Msg 4"

    def test_get_messages_returns_list_not_deque(self):
        history = History(max_size=5)
        history.add_user_message("Test")

        messages = history.get_messages()
        assert isinstance(messages, list)
        assert not isinstance(messages, type(history._messages))
