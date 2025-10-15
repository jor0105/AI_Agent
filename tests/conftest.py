"""
Configuração global do pytest.

Este arquivo contém fixtures compartilhadas por todos os testes.
"""

from unittest.mock import Mock

import pytest

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.entities.agent_domain import Agent
from src.domain.value_objects import History

# ============================================================================
# FIXTURES GLOBAIS
# ============================================================================


@pytest.fixture
def mock_chat_repository():
    """
    Mock do ChatRepository para testes.

    Returns:
        Mock configurado do ChatRepository
    """
    mock = Mock(spec=ChatRepository)
    mock.chat.return_value = "Mocked AI response"
    return mock


@pytest.fixture
def sample_agent():
    """
    Agente de exemplo para testes.

    Returns:
        Agent: Instância configurada de Agent
    """
    return Agent(
        provider="openai",
        model="gpt-5-nano",
        name="Test Agent",
        instructions="You are a test agent",
    )


@pytest.fixture
def sample_agent_with_history():
    """
    Agente com histórico pré-populado.

    Returns:
        Agent: Instância com histórico
    """
    agent = Agent(
        provider="openai",
        model="gpt-5-nano",
        name="Agent with History",
        instructions="Test agent with history",
    )
    agent.add_user_message("Hello")
    agent.add_assistant_message("Hi there!")
    agent.add_user_message("How are you?")
    agent.add_assistant_message("I'm doing well!")
    return agent


@pytest.fixture
def empty_history():
    """
    Histórico vazio para testes.

    Returns:
        History: Instância vazia
    """
    return History()


@pytest.fixture
def populated_history():
    """
    Histórico pré-populado para testes.

    Returns:
        History: Instância com mensagens
    """
    history = History()
    history.add_user_message("Message 1")
    history.add_assistant_message("Response 1")
    history.add_user_message("Message 2")
    history.add_assistant_message("Response 2")
    return history


# ============================================================================
# CONFIGURAÇÕES DO PYTEST
# ============================================================================


def pytest_configure(config):
    """Configuração executada antes dos testes."""
    config.addinivalue_line("markers", "unit: marca teste como unitário")
    config.addinivalue_line("markers", "integration: marca teste como integração")
    config.addinivalue_line("markers", "slow: marca teste como lento")
