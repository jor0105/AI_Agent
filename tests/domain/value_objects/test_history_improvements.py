import pytest

from src.domain.value_objects.history import History


@pytest.mark.unit
class TestHistoryMaxSizeValidation:
    """Testes para validação do max_size."""

    def test_history_with_valid_max_size(self):
        history = History(max_size=5)
        assert history.max_size == 5

    def test_history_with_zero_max_size_raises_error(self):
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size=0)

    def test_history_with_negative_max_size_raises_error(self):
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size=-1)

    def test_history_with_str_raises_error(self):
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size="Test")

    def test_history_with_null_raises_error(self):
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size="")

    def test_history_with_float_raises_error(self):
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History(max_size=1.5)

    def test_history_with_large_max_size(self):
        history = History(max_size=1000)
        assert history.max_size == 1000

    def test_from_dict_list_with_invalid_max_size(self):
        data = [{"role": "user", "content": "Test"}]
        with pytest.raises(
            ValueError, match="Tamanho máximo do histórico deve ser maior que zero"
        ):
            History.from_dict_list(data, max_size=0)


@pytest.mark.unit
class TestHistoryDequePerformance:
    """Testes para verificar uso de deque no History."""

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
