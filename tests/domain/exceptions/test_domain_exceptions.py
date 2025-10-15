import pytest

from src.domain.exceptions.domain_exceptions import (
    AdapterNotFoundException,
    AgentException,
    ChatException,
    InvalidAgentConfigException,
    InvalidModelException,
)


@pytest.mark.unit
class TestAgentException:
    """Testes para AgentException (exceção base)."""

    def test_create_agent_exception(self):
        exception = AgentException("Test error")

        assert str(exception) == "Test error"
        assert exception.message == "Test error"

    def test_agent_exception_is_exception(self):
        exception = AgentException("Test")

        assert isinstance(exception, Exception)

    def test_raise_agent_exception(self):
        with pytest.raises(AgentException, match="Test error"):
            raise AgentException("Test error")


@pytest.mark.unit
class TestInvalidAgentConfigException:
    """Testes para InvalidAgentConfigException."""

    def test_create_with_field_and_reason(self):
        exception = InvalidAgentConfigException("model", "cannot be empty")

        assert "model" in str(exception)
        assert "cannot be empty" in str(exception)
        assert "Configuração inválida" in str(exception)

    def test_exception_message_format(self):
        exception = InvalidAgentConfigException("name", "too short")
        expected = "Configuração inválida no campo 'name': too short"

        assert str(exception) == expected

    def test_is_agent_exception(self):
        exception = InvalidAgentConfigException("test", "reason")

        assert isinstance(exception, AgentException)
        assert isinstance(exception, Exception)

    def test_raise_invalid_config_exception(self):
        with pytest.raises(InvalidAgentConfigException):
            raise InvalidAgentConfigException("field", "reason")

    def test_catch_as_agent_exception(self):
        with pytest.raises(AgentException):
            raise InvalidAgentConfigException("field", "reason")


@pytest.mark.unit
class TestInvalidModelException:
    """Testes para InvalidModelException."""

    def test_create_with_model_name(self):
        exception = InvalidModelException("invalid_model")

        assert "invalid_model" in str(exception)
        assert "não suportado" in str(exception)

    def test_exception_message_format(self):
        exception = InvalidModelException("gpt-5")
        expected = "Modelo de IA não suportado: 'gpt-5'"

        assert str(exception) == expected

    def test_is_agent_exception(self):
        exception = InvalidModelException("test")

        assert isinstance(exception, AgentException)
        assert isinstance(exception, Exception)

    def test_raise_invalid_model_exception(self):
        with pytest.raises(InvalidModelException):
            raise InvalidModelException("unknown_model")

    def test_with_different_model_names(self):
        models = ["invalid", "gpt-999", "unknown_llm"]

        for model in models:
            exception = InvalidModelException(model)
            assert model in str(exception)


@pytest.mark.unit
class TestChatException:
    """Testes para ChatException (exceção de comunicação)."""

    def test_create_with_message_only(self):
        exception = ChatException("Communication error")

        assert str(exception) == "Communication error"
        assert exception.message == "Communication error"
        assert exception.original_error is None

    def test_create_with_original_error(self):
        original = ValueError("Original error")
        exception = ChatException("Wrapped error", original)

        assert exception.message == "Wrapped error"
        assert exception.original_error is original

    def test_is_base_exception(self):
        exception = ChatException("Test")

        assert isinstance(exception, Exception)
        assert not isinstance(exception, AgentException)

    def test_raise_chat_exception(self):
        with pytest.raises(ChatException, match="Test error"):
            raise ChatException("Test error")

    def test_preserve_original_error_context(self):
        original = ConnectionError("Network failed")
        exception = ChatException("Failed to connect", original)

        assert isinstance(exception.original_error, ConnectionError)
        assert str(exception.original_error) == "Network failed"


@pytest.mark.unit
class TestAdapterNotFoundException:
    """Testes para AdapterNotFoundException."""

    def test_create_with_adapter_name(self):
        exception = AdapterNotFoundException("CustomAdapter")

        assert "CustomAdapter" in str(exception)
        assert "não encontrado" in str(exception)

    def test_exception_message_format(self):
        exception = AdapterNotFoundException("TestAdapter")
        expected = "Adapter não encontrado: 'TestAdapter'"

        assert str(exception) == expected

    def test_is_chat_exception(self):
        exception = AdapterNotFoundException("test")

        assert isinstance(exception, ChatException)
        assert isinstance(exception, Exception)

    def test_raise_adapter_not_found_exception(self):
        with pytest.raises(AdapterNotFoundException):
            raise AdapterNotFoundException("MissingAdapter")

    def test_catch_as_chat_exception(self):
        with pytest.raises(ChatException):
            raise AdapterNotFoundException("test")

    def test_with_different_adapter_names(self):
        adapters = ["OpenAI", "Ollama", "CustomAdapter"]

        for adapter in adapters:
            exception = AdapterNotFoundException(adapter)
            assert adapter in str(exception)


@pytest.mark.unit
class TestExceptionHierarchy:
    """Testes da hierarquia de exceções."""

    def test_agent_exceptions_hierarchy(self):
        config_exc = InvalidAgentConfigException("field", "reason")
        assert isinstance(config_exc, AgentException)

        model_exc = InvalidModelException("model")
        assert isinstance(model_exc, AgentException)

    def test_chat_exceptions_hierarchy(self):
        adapter_exc = AdapterNotFoundException("adapter")
        assert isinstance(adapter_exc, ChatException)

    def test_independent_exception_trees(self):
        agent_exc = AgentException("test")
        chat_exc = ChatException("test")

        assert not isinstance(agent_exc, ChatException)
        assert not isinstance(chat_exc, AgentException)

    def test_all_exceptions_are_exception(self):
        exceptions = [
            AgentException("test"),
            InvalidAgentConfigException("field", "reason"),
            InvalidModelException("model"),
            ChatException("test"),
            AdapterNotFoundException("adapter"),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_catch_specific_exceptions(self):
        with pytest.raises(InvalidAgentConfigException):
            raise InvalidAgentConfigException("field", "reason")

        with pytest.raises(InvalidModelException):
            raise InvalidModelException("model")

        with pytest.raises(AdapterNotFoundException):
            raise AdapterNotFoundException("adapter")

    def test_catch_base_exceptions(self):
        with pytest.raises(AgentException):
            raise InvalidAgentConfigException("field", "reason")

        with pytest.raises(ChatException):
            raise AdapterNotFoundException("adapter")
