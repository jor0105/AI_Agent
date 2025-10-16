"""
Configuração global do pytest.

Este arquivo contém fixtures compartilhadas por todos os testes da aplicação.
Organiza fixtures por categoria e fornece dados de teste reutilizáveis.
"""

from unittest.mock import Mock

import pytest

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.entities.agent_domain import Agent
from src.domain.value_objects import History

# ============================================================================
# CONSTANTES
# ============================================================================

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_TEST_AGENT_NAME = "Test Agent"
DEFAULT_TEST_INSTRUCTIONS = "You are a test agent"
MOCKED_AI_RESPONSE = "Mocked AI response"


# ============================================================================
# FIXTURES - REPOSITÓRIOS
# ============================================================================


@pytest.fixture
def mock_chat_repository():
    """
    Mock do ChatRepository para testes.

    Fornece um mock totalmente configurado do ChatRepository com resposta
    padrão para operações de chat.

    Returns:
        Mock: Mock configurado do ChatRepository
    """
    mock = Mock(spec=ChatRepository)
    mock.chat.return_value = MOCKED_AI_RESPONSE
    return mock


# ============================================================================
# FIXTURES - ENTIDADES
# ============================================================================


@pytest.fixture
def sample_agent():
    """
    Agente de exemplo básico para testes.

    Fornece uma instância padrão de Agent com configurações mínimas
    necessárias para testes unitários.

    Returns:
        Agent: Instância configurada de Agent
    """
    return Agent(
        provider=DEFAULT_PROVIDER,
        model=DEFAULT_MODEL,
        name=DEFAULT_TEST_AGENT_NAME,
        instructions=DEFAULT_TEST_INSTRUCTIONS,
    )


@pytest.fixture
def sample_agent_with_history(sample_agent):
    """
    Agente com histórico pré-populado para testes.

    Estende a fixture sample_agent adicionando histórico de conversas
    para testes que validam comportamento com contexto prévio.

    Args:
        sample_agent: Fixture base de agente

    Returns:
        Agent: Instância com histórico de conversas
    """
    sample_agent.add_user_message("Hello")
    sample_agent.add_assistant_message("Hi there!")
    sample_agent.add_user_message("How are you?")
    sample_agent.add_assistant_message("I'm doing well!")
    return sample_agent


# ============================================================================
# FIXTURES - HISTÓRICO
# ============================================================================


@pytest.fixture
def empty_history():
    """
    Histórico vazio para testes.

    Fornece uma instância limpa de History para testes que validam
    comportamento inicial sem mensagens prévias.

    Returns:
        History: Instância vazia de History
    """
    return History()


@pytest.fixture
def populated_history():
    """
    Histórico pré-populado com mensagens de exemplo.

    Fornece uma instância de History com conversas de exemplo para testes
    que validam processamento de histórico com múltiplas mensagens.

    Returns:
        History: Instância com mensagens pré-configuradas
    """
    history = History()
    history.add_user_message("Message 1")
    history.add_assistant_message("Response 1")
    history.add_user_message("Message 2")
    history.add_assistant_message("Response 2")
    return history

    history.add_assistant_message("Response 2")


# ============================================================================
# CONFIGURAÇÕES DO PYTEST
# ============================================================================


def pytest_configure(config):
    """
    Configuração executada antes dos testes.

    Registra marcadores customizados para categorizar e filtrar testes.
    """
    markers = [
        ("unit", "marca teste como unitário - testes de componentes isolados"),
        (
            "integration",
            "marca teste como integração - testes com múltiplos componentes",
        ),
        ("slow", "marca teste como lento - testes que demandam mais tempo"),
    ]

    for marker_name, marker_description in markers:
        config.addinivalue_line("markers", f"{marker_name}: {marker_description}")
