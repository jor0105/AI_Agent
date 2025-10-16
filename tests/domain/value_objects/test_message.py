import pytest

from src.domain.value_objects.message import Message, MessageRole


@pytest.mark.unit
class TestMessageRole:
    """Testes para o enum MessageRole."""

    def test_message_role_values(self):
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_message_role_string_representation(self):
        assert str(MessageRole.USER) == "user"
        assert str(MessageRole.ASSISTANT) == "assistant"
        assert str(MessageRole.SYSTEM) == "system"


@pytest.mark.unit
class TestMessage:
    """Testes para o Value Object Message."""

    def test_create_message_with_valid_data(self):
        message = Message(role=MessageRole.USER, content="Hello")

        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_create_user_message(self):
        message = Message(role=MessageRole.USER, content="User message")

        assert message.role == MessageRole.USER
        assert message.content == "User message"

    def test_create_assistant_message(self):
        message = Message(role=MessageRole.ASSISTANT, content="Assistant response")

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Assistant response"

    def test_create_system_message(self):
        message = Message(role=MessageRole.SYSTEM, content="System instruction")

        assert message.role == MessageRole.SYSTEM
        assert message.content == "System instruction"

    def test_message_is_immutable(self):
        message = Message(role=MessageRole.USER, content="Test")

        with pytest.raises(AttributeError):
            message.content = "New content"

    def test_message_validation_empty_content(self):
        with pytest.raises(
            ValueError, match="O conteúdo da mensagem não pode estar vazio"
        ):
            Message(role=MessageRole.USER, content="")

    def test_message_validation_whitespace_content(self):
        with pytest.raises(
            ValueError, match="O conteúdo da mensagem não pode estar vazio"
        ):
            Message(role=MessageRole.USER, content="   ")

    def test_message_validation_invalid_role_type(self):
        with pytest.raises(
            ValueError, match="Role deve ser uma instância de MessageRole"
        ):
            Message(role="user", content="Hello")

    def test_to_dict_conversion(self):
        message = Message(role=MessageRole.USER, content="Hello")
        result = message.to_dict()

        assert result == {"role": "user", "content": "Hello"}
        assert isinstance(result, dict)

    def test_from_dict_with_valid_data(self):
        data = {"role": "user", "content": "Hello"}
        message = Message.from_dict(data)

        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_from_dict_all_roles(self):
        roles = ["user", "assistant", "system"]

        for role in roles:
            data = {"role": role, "content": "Test"}
            message = Message.from_dict(data)
            assert message.role.value == role

    def test_from_dict_missing_role(self):
        data = {"content": "Hello"}

        with pytest.raises(
            ValueError, match="Dicionário deve conter 'role' e 'content'"
        ):
            Message.from_dict(data)

    def test_from_dict_missing_content(self):
        data = {"role": "user"}

        with pytest.raises(
            ValueError, match="Dicionário deve conter 'role' e 'content'"
        ):
            Message.from_dict(data)

    def test_from_dict_invalid_role(self):
        data = {"role": "invalid_role", "content": "Hello"}

        with pytest.raises(ValueError, match="Role inválido"):
            Message.from_dict(data)

    def test_message_equality(self):
        msg1 = Message(role=MessageRole.USER, content="Hello")
        msg2 = Message(role=MessageRole.USER, content="Hello")
        msg3 = Message(role=MessageRole.USER, content="Different")

        assert msg1 == msg2
        assert msg1 != msg3

    def test_to_dict_and_from_dict_roundtrip(self):
        original = Message(role=MessageRole.ASSISTANT, content="Test message")
        dict_form = original.to_dict()
        reconstructed = Message.from_dict(dict_form)

        assert original == reconstructed

    def test_message_with_long_content(self):
        long_content = "A" * 10000
        message = Message(role=MessageRole.USER, content=long_content)

        assert message.content == long_content
        assert len(message.content) == 10000

    def test_message_with_special_characters(self):
        special_content = "Hello! 你好 🎉 @#$%^&*()"
        message = Message(role=MessageRole.USER, content=special_content)

        assert message.content == special_content

    def test_message_with_newlines(self):
        multiline_content = "Line 1\nLine 2\nLine 3"
        message = Message(role=MessageRole.USER, content=multiline_content)

        assert message.content == multiline_content
        assert "\n" in message.content
