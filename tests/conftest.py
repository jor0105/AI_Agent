import os
from unittest.mock import Mock, patch

import pytest

from createagents.application.interfaces import ChatRepository
from createagents.domain.entities import History
from createagents.domain.entities.agent_domain import Agent
from tests.test_constants import OPENAI_MODEL_NANO

DEFAULT_PROVIDER = 'openai'
DEFAULT_TEST_AGENT_NAME = 'Test Agent'
DEFAULT_TEST_INSTRUCTIONS = 'You are a test agent'
MOCKED_AI_RESPONSE = 'Mocked AI response'


@pytest.fixture(autouse=True)
def configure_logging():
    """Configures logging for all tests."""
    import logging

    from createagents.infra.config.logging_config import LoggingConfig

    # Configure logging for tests to ensure we can see output if needed
    # Using DEBUG level by default for tests to catch everything
    LoggingConfig.configure_for_development(level=logging.DEBUG)

    yield

    # Reset logging after test
    LoggingConfig.reset()


@pytest.fixture
def mock_chat_repository():
    mock = Mock(spec=ChatRepository)
    mock.chat.return_value = MOCKED_AI_RESPONSE
    return mock


@pytest.fixture
def sample_agent():
    return Agent(
        provider=DEFAULT_PROVIDER,
        model=OPENAI_MODEL_NANO,
        name=DEFAULT_TEST_AGENT_NAME,
        instructions=DEFAULT_TEST_INSTRUCTIONS,
    )


@pytest.fixture
def sample_agent_with_history(sample_agent):
    sample_agent.add_user_message('Hello')
    sample_agent.add_assistant_message('Hi there!')
    sample_agent.add_user_message('How are you?')
    sample_agent.add_assistant_message("I'm doing well!")
    return sample_agent


@pytest.fixture
def empty_history():
    return History()


@pytest.fixture
def populated_history():
    history = History()
    history.add_user_message('Message 1')
    history.add_assistant_message('Response 1')
    history.add_user_message('Message 2')
    history.add_assistant_message('Response 2')
    return history


@pytest.fixture(autouse=True)
def mock_openai_api_key(request):
    """
    Automatically mock OPENAI_API_KEY and OpenAI client for all unit tests.

    This prevents tests from failing in CI/CD environments where the actual
    API key is not available. Integration tests are excluded from this mock
    so they can test real API interactions.

    Tests that specifically test the ClientOpenAI class are also excluded
    since they provide their own mocks.
    """
    # Only apply to unit tests, not integration tests
    if 'unit' in request.keywords:
        from unittest.mock import MagicMock

        # Skip if the test is in test_client_openai.py (those tests mock OpenAI themselves)
        if 'test_client_openai' in request.node.nodeid:
            yield
            return

        with (
            patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-mock'}),
            patch(
                'createagents.infra.adapters.openai.client_openai.ClientOpenAI.get_client'
            ) as mock_get_client,
        ):
            # Create a mock OpenAI client
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            yield
    else:
        yield


def pytest_configure(config):
    markers = [
        ('unit', 'marks the test as unit - isolated component tests'),
        (
            'integration',
            'marks the test as integration - tests with multiple components',
        ),
        ('slow', 'marks the test as slow - tests that take longer'),
    ]

    for marker_name, marker_description in markers:
        config.addinivalue_line(
            'markers', f'{marker_name}: {marker_description}'
        )
