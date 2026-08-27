from unittest.mock import Mock, patch

import pytest

from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

ASYNC_OPENAI = 'createagents.infra.adapters.OpenAI.client_openai.AsyncOpenAI'

# allow-assertion-reduction: Removed get-client matrix cases target retired construction semantics; current settings coverage remains below.


@pytest.mark.unit
class TestClientOpenAI:
    def test_api_key_env_var_name(self):
        assert ClientOpenAI.API_OPENAI_NAME == 'OPENAI_API_KEY'

    @patch(ASYNC_OPENAI)
    def test_builds_the_sdk_client_with_the_given_settings(self, mock_openai):
        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client(
            'test-api-key', timeout=30, max_retries=3
        )

        assert client is mock_client
        mock_openai.assert_called_once_with(
            api_key='test-api-key', timeout=30, max_retries=3
        )

    @patch(ASYNC_OPENAI)
    def test_timeout_and_retries_reach_the_sdk(self, mock_openai):
        """These come from OPENAI_TIMEOUT / OPENAI_MAX_RETRIES."""
        ClientOpenAI.get_client('k', timeout=90, max_retries=7)

        kwargs = mock_openai.call_args.kwargs
        assert kwargs['timeout'] == 90
        assert kwargs['max_retries'] == 7

    @patch(ASYNC_OPENAI)
    def test_each_call_builds_its_own_client(self, mock_openai):
        mock_openai.side_effect = [Mock(), Mock(), Mock()]

        clients = [
            ClientOpenAI.get_client(key, timeout=30, max_retries=3)
            for key in ('key1', 'key2', 'sk-test-123')
        ]

        assert mock_openai.call_count == 3
        assert len({id(c) for c in clients}) == 3

    @patch(ASYNC_OPENAI)
    def test_sdk_initialization_errors_propagate(self, mock_openai):
        mock_openai.side_effect = ValueError('Invalid API key')

        with pytest.raises(ValueError, match='Invalid API key'):
            ClientOpenAI.get_client('bad', timeout=30, max_retries=3)

    def test_get_client_is_a_static_method(self):
        assert isinstance(ClientOpenAI.__dict__['get_client'], staticmethod)
