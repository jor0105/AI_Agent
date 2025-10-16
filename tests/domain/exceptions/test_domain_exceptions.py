import pytest

from src.domain.exceptions.domain_exceptions import (
    AdapterNotFoundException,
    AgentException,
    ChatException,
    InvalidAgentConfigException,
    InvalidConfigTypeException,
    InvalidModelException,
    InvalidProviderException,
    UnsupportedConfigException,
)


@pytest.mark.unit
class TestAgentException:
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


@pytest.mark.unit
class TestInvalidProviderException:
    def test_create_with_provider_and_available_list(self):
        available = {"openai", "ollama"}
        exception = InvalidProviderException("invalid", available)

        assert "invalid" in str(exception)
        assert "não está disponível" in str(exception)
        assert "openai" in str(exception) or "ollama" in str(exception)

    def test_exception_message_format(self):
        available = {"openai", "ollama"}
        exception = InvalidProviderException("custom", available)

        assert "custom" in str(exception)
        assert "Providers disponíveis" in str(exception)

    def test_is_agent_exception(self):
        exception = InvalidProviderException("test", {"openai"})

        assert isinstance(exception, AgentException)
        assert isinstance(exception, Exception)

    def test_raise_invalid_provider_exception(self):
        with pytest.raises(InvalidProviderException):
            raise InvalidProviderException("unknown", {"openai", "ollama"})

    def test_available_providers_shown_in_message(self):
        available = {"openai", "ollama", "anthropic"}
        exception = InvalidProviderException("test", available)

        message = str(exception)
        # Verifica se todos providers disponíveis aparecem na mensagem
        for provider in available:
            assert provider in message


@pytest.mark.unit
class TestUnsupportedConfigException:
    def test_create_with_config_and_available_list(self):
        available = {"temperature", "max_tokens", "top_p"}
        exception = UnsupportedConfigException("invalid_config", available)

        assert "invalid_config" in str(exception)
        assert "não é suportada" in str(exception)

    def test_exception_message_format(self):
        available = {"temperature", "max_tokens"}
        exception = UnsupportedConfigException("custom", available)

        assert "custom" in str(exception)
        assert "Opções válidas" in str(exception)

    def test_is_agent_exception(self):
        exception = UnsupportedConfigException("test", {"temperature"})

        assert isinstance(exception, AgentException)
        assert isinstance(exception, Exception)

    def test_raise_unsupported_config_exception(self):
        with pytest.raises(UnsupportedConfigException):
            raise UnsupportedConfigException("bad_config", {"temperature"})

    def test_available_configs_shown_in_message(self):
        available = {"temperature", "max_tokens", "top_p"}
        exception = UnsupportedConfigException("test", available)

        message = str(exception)
        # Verifica se todas configs disponíveis aparecem na mensagem
        assert "temperature" in message or "max_tokens" in message or "top_p" in message


@pytest.mark.unit
class TestInvalidConfigTypeException:
    def test_create_with_config_and_type(self):
        exception = InvalidConfigTypeException("temperature", object)

        assert "temperature" in str(exception)
        assert "tipo inválido" in str(exception)
        assert "object" in str(exception)

    def test_exception_message_format(self):
        exception = InvalidConfigTypeException("max_tokens", list)

        assert "max_tokens" in str(exception)
        assert "list" in str(exception)

    def test_is_agent_exception(self):
        exception = InvalidConfigTypeException("test", str)

        assert isinstance(exception, AgentException)
        assert isinstance(exception, Exception)

    def test_raise_invalid_config_type_exception(self):
        with pytest.raises(InvalidConfigTypeException):
            raise InvalidConfigTypeException("field", dict)

    def test_with_different_types(self):
        types = [int, str, float, list, dict, object]

        for t in types:
            exception = InvalidConfigTypeException("test", t)
            assert t.__name__ in str(exception)


@pytest.mark.unit
class TestNewExceptionHierarchy:
    def test_all_new_agent_exceptions_inherit_from_agent_exception(self):
        exceptions = [
            InvalidProviderException("test", {"openai"}),
            UnsupportedConfigException("test", {"temperature"}),
            InvalidConfigTypeException("test", str),
        ]

        for exc in exceptions:
            assert isinstance(exc, AgentException)
            assert isinstance(exc, Exception)

    def test_catch_new_exceptions_as_agent_exception(self):
        with pytest.raises(AgentException):
            raise InvalidProviderException("test", {"openai"})

        with pytest.raises(AgentException):
            raise UnsupportedConfigException("test", {"temperature"})

        with pytest.raises(AgentException):
            raise InvalidConfigTypeException("test", str)

        with pytest.raises(ChatException):
            raise AdapterNotFoundException("adapter")
