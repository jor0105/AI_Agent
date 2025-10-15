"""
Testes unitários para ClientOpenAI.

Testa criação do cliente OpenAI.
"""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestClientOpenAI:
    """Testes para ClientOpenAI."""

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_creates_client_with_api_key(self, mock_openai):
        """Testa criação do cliente com API key."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("test-api-key")

        assert client is mock_client
        mock_openai.assert_called_once_with(api_key="test-api-key")

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_returns_openai_instance(self, mock_openai):
        """Testa que retorna instância de OpenAI."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("any-key")

        assert client is not None

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_with_different_keys(self, mock_openai):
        """Testa criação com diferentes API keys."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        keys = ["key1", "key2", "sk-test-123"]

        for key in keys:
            ClientOpenAI.get_client(key)

        assert mock_openai.call_count == len(keys)

    def test_api_openai_name_constant(self):
        """Testa constante do nome da API key."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert ClientOpenAI.API_OPENAI_NAME == "OPENAI_API_KEY"

    @patch("src.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_is_static_method(self, mock_openai):
        """Testa que get_client é método estático."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Pode ser chamado sem instanciar a classe
        client = ClientOpenAI.get_client("test-key")

        assert client is not None
