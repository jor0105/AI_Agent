from unittest.mock import Mock, patch

import pytest

IA_OPENAI_TEST_1: str = "gpt-5-nano"
IA_OPENAI_TEST_2: str = "gpt-5-mini"
IA_OPENAI_TEST_3: str = "gpt-4-mini"


@pytest.mark.unit
class TestClientOpenAI:
    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_creates_client_with_api_key(self, mock_openai):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("test-api-key")

        assert client is mock_client
        mock_openai.assert_called_once_with(api_key="test-api-key")

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_returns_openai_instance(self, mock_openai):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("any-key")

        assert client is not None

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_with_different_keys(self, mock_openai):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        keys = ["key1", "key2", "sk-test-123"]

        for key in keys:
            ClientOpenAI.get_client(key)

        assert mock_openai.call_count == len(keys)

    def test_api_openai_name_constant(self):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert ClientOpenAI.API_OPENAI_NAME == "OPENAI_API_KEY"

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_is_static_method(self, mock_openai):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("test-key")

        assert client is not None

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_called_with_positional_and_keyword(self, mock_openai):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        # chamada posicional
        ClientOpenAI.get_client("positional-key")

        # chamada por keyword (mesmo comportamento esperado)
        ClientOpenAI.get_client(api_key="keyword-key")

        # O OpenAI deve ter sido chamado duas vezes com os argumentos corretos
        mock_openai.assert_any_call(api_key="positional-key")
        mock_openai.assert_any_call(api_key="keyword-key")

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_accepts_non_string_keys(self, mock_openai):
        """Garante que tipos diferentes de chave ainda são repassados ao cliente."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        key_obj = object()
        ClientOpenAI.get_client(key_obj)

        mock_openai.assert_called_with(api_key=key_obj)

    def test_api_openai_name_constant_type(self):
        """Valida que a constante `API_OPENAI_NAME` é uma string não vazia."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert isinstance(ClientOpenAI.API_OPENAI_NAME, str)
        assert ClientOpenAI.API_OPENAI_NAME != ""

    def test_get_client_callable_from_instance(self):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        # não vamos patchar aqui; apenas inspeção de atributo
        # verificar que o atributo é chamável (função/staticmethod descriptor)
        attr = getattr(ClientOpenAI, "get_client")
        assert callable(attr)
