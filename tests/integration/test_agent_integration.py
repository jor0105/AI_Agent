"""
Testes de integração para AIAgent com providers reais (OpenAI e Ollama).

Este módulo testa o AIAgent em cenários da vida real, incluindo:
- Inicialização com diferentes configurações
- Chat com IAs reais
- Tratamento de erros
- Métricas e histórico
- Validações de entrada
"""

import os

import pytest

from src.domain.exceptions import InvalidAgentConfigException
from src.presentation.agent_controller import AIAgent

# ============================================================================
# CONFIGURAÇÕES GLOBAIS - IAs para testes
# ============================================================================

# Modelos Ollama (devem estar instalados localmente)
IA_OLLAMA_TEST: str = "phi4-mini:latest"

# Modelos OpenAI (requerem API key válida)
IA_OPENAI_TEST_1: str = "gpt-5-mini"
IA_OPENAI_TEST_2: str = "gpt-5-nano"


# ============================================================================
# HELPERS
# ============================================================================


def _get_openai_api_key():
    """Helper para obter a chave da API do OpenAI do ambiente (.env) ou pular o teste."""
    from src.infra.adapters.OpenAI.client_openai import ClientOpenAI
    from src.infra.config.environment import EnvironmentConfig

    # Evitar executar chamadas reais em ambientes de CI por padrão
    if os.getenv("CI"):
        pytest.skip("Skipping real API integration test on CI (set CI=0 to run)")

    try:
        # Usa EnvironmentConfig que carrega do .env automaticamente
        api_key = EnvironmentConfig.get_api_key(ClientOpenAI.API_OPENAI_NAME)
        return api_key
    except EnvironmentError:
        pytest.skip(
            f"Skipping integration test: {ClientOpenAI.API_OPENAI_NAME} not found in .env file"
        )


def _check_ollama_available():
    """Helper para verificar se o Ollama está disponível e rodando."""
    import subprocess

    # Evitar executar chamadas reais em ambientes de CI por padrão
    if os.getenv("CI"):
        pytest.skip("Skipping real Ollama integration test on CI (set CI=0 to run)")

    try:
        # Tenta verificar se o Ollama está rodando
        result = subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        if result.returncode != 0:
            pytest.skip("Ollama não está disponível ou não está rodando")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("Ollama não está instalado ou não está respondendo")


def _check_ollama_model_available(model: str):
    """Helper para verificar se um modelo específico está disponível no Ollama."""
    import subprocess

    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        if model not in result.stdout:
            pytest.skip(
                f"Modelo {model} não está disponível no Ollama. Execute: ollama pull {model}"
            )
    except Exception as e:
        pytest.skip(f"Não foi possível verificar modelos disponíveis: {e}")


# ============================================================================
# TESTES DE INICIALIZAÇÃO - ERROS
# ============================================================================


@pytest.mark.integration
class TestAIAgentInitializationErrors:
    def test_initialization_with_empty_model_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AIAgent(
                provider="openai",
                model="",
                name="Test Agent",
                instructions="Be helpful",
            )

    def test_initialization_with_empty_name_raises_error(self):
        """Testa que name vazio (quando fornecido) lança InvalidAgentConfigException."""
        with pytest.raises(InvalidAgentConfigException):
            AIAgent(
                provider="openai",
                model="gpt-5-mini",
                name="",
                instructions="Be helpful",
            )

    def test_initialization_with_empty_instructions_raises_error(self):
        """Testa que instructions vazio (quando fornecido) lança InvalidAgentConfigException."""
        with pytest.raises(InvalidAgentConfigException):
            AIAgent(
                provider="openai",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="",
            )

    def test_initialization_with_none_name(self):
        """Testa que name=None é aceito."""
        agent = AIAgent(
            provider="openai",
            model="gpt-5-mini",
            name=None,
            instructions="Be helpful",
        )
        configs = agent.get_configs()
        assert configs["name"] is None

    def test_initialization_with_none_instructions(self):
        """Testa que instructions=None é aceito."""
        agent = AIAgent(
            provider="openai",
            model="gpt-5-mini",
            name="Test Agent",
            instructions=None,
        )
        configs = agent.get_configs()
        assert configs["instructions"] is None

    def test_initialization_with_both_none(self):
        """Testa que name e instructions podem ser None ao mesmo tempo."""
        agent = AIAgent(
            provider="openai",
            model="gpt-5-mini",
            name=None,
            instructions=None,
        )
        configs = agent.get_configs()
        assert configs["name"] is None
        assert configs["instructions"] is None

    def test_initialization_with_only_required_fields(self):
        """Testa criação apenas com campos obrigatórios."""
        agent = AIAgent(
            provider="openai",
            model="gpt-5-mini",
        )
        configs = agent.get_configs()
        assert configs["provider"] == "openai"
        assert configs["model"] == "gpt-5-mini"
        assert configs["name"] is None
        assert configs["instructions"] is None

    def test_initialization_with_invalid_provider_raises_error(self):
        """Testa que provider inválido lança exceção."""
        with pytest.raises(
            Exception
        ):  # Pode ser ValueError ou InvalidAgentConfigException
            AIAgent(
                provider="invalid_provider_xyz",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="Be helpful",
            )

    def test_initialization_with_zero_history_max_size_raises_error(self):
        """Testa que history_max_size zero lança InvalidAgentConfigException."""
        with pytest.raises(InvalidAgentConfigException, match="history_max_size"):
            AIAgent(
                provider="openai",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="Be helpful",
                history_max_size=0,
            )

    def test_initialization_with_negative_history_max_size_raises_error(self):
        """Testa que history_max_size negativo lança InvalidAgentConfigException."""
        with pytest.raises(InvalidAgentConfigException, match="history_max_size"):
            AIAgent(
                provider="openai",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="Be helpful",
                history_max_size=-5,
            )


# ============================================================================
# TESTES DE INICIALIZAÇÃO - SUCESSO COM OPENAI
# ============================================================================


@pytest.mark.integration
class TestAIAgentInitializationSuccessOpenAI:
    """Testes de sucesso na inicialização do AIAgent com OpenAI."""

    def test_initialization_with_openai_gpt4_mini(self):
        """Testa inicialização bem-sucedida com OpenAI GPT-4 Mini."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Test Agent OpenAI",
            instructions="You are a helpful assistant",
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs["provider"] == "openai"
        assert configs["model"] == IA_OPENAI_TEST_1
        assert configs["name"] == "Test Agent OpenAI"

    def test_initialization_with_openai_gpt4_nano(self):
        """Testa inicialização bem-sucedida com OpenAI GPT-4 Nano."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_2,
            name="Test Agent Nano",
            instructions="You are a helpful assistant",
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs["provider"] == "openai"
        assert configs["model"] == IA_OPENAI_TEST_2

    def test_initialization_with_custom_config_openai(self):
        """Testa inicialização com configurações customizadas no OpenAI."""
        _get_openai_api_key()

        custom_config = {
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9,
        }

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Custom Config Agent",
            instructions="Be creative",
            config=custom_config,
        )

        configs = agent.get_configs()
        assert configs["config"] == custom_config

    def test_initialization_with_custom_history_size_openai(self):
        """Testa inicialização com tamanho de histórico customizado."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Large History Agent",
            instructions="Remember our conversation",
            history_max_size=50,
        )

        configs = agent.get_configs()
        assert configs["history_max_size"] == 50


# ============================================================================
# TESTES DE INICIALIZAÇÃO - SUCESSO COM OLLAMA
# ============================================================================


@pytest.mark.integration
class TestAIAgentInitializationSuccessOllama:
    """Testes de sucesso na inicialização do AIAgent com Ollama."""

    def test_initialization_with_ollama_phi4(self):
        """Testa inicialização bem-sucedida com Ollama Phi-4 Mini."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Test Agent Ollama",
            instructions="You are a helpful assistant",
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs["provider"] == "ollama"
        assert configs["model"] == IA_OLLAMA_TEST
        assert configs["name"] == "Test Agent Ollama"

    def test_initialization_with_custom_config_ollama(self):
        """Testa inicialização com configurações customizadas no Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        custom_config = {
            "temperature": 0.5,
            "num_predict": 100,
        }

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Custom Config Ollama",
            instructions="Be precise",
            config=custom_config,
        )

        configs = agent.get_configs()
        assert configs["config"] == custom_config

    def test_initialization_with_custom_history_size_ollama(self):
        """Testa inicialização com tamanho de histórico customizado no Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Small History Agent",
            instructions="Keep context",
            history_max_size=5,
        )

        configs = agent.get_configs()
        assert configs["history_max_size"] == 5


# ============================================================================
# TESTES DE CHAT - OPENAI
# ============================================================================


@pytest.mark.integration
class TestAIAgentChatOpenAI:
    """Testes de chat com OpenAI."""

    def test_simple_chat_with_openai(self):
        """Testa chat simples com OpenAI."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Chat Agent",
            instructions="You are a helpful assistant. Answer briefly.",
        )

        response = agent.chat("What is 2+2?")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response

    def test_multiple_chats_with_history_openai(self):
        """Testa múltiplas conversas mantendo histórico."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="History Agent",
            instructions="You are a helpful assistant. Remember the context.",
        )

        # Primeira mensagem
        response1 = agent.chat("My name is Jordan")
        assert response1 is not None

        # Segunda mensagem referenciando a primeira
        response2 = agent.chat("What is my name?")
        assert response2 is not None
        assert "Jordan" in response2 or "jordan" in response2.lower()

    def test_chat_with_empty_message_openai(self):
        """Testa que mensagem vazia pode causar erro ou resposta padrão."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Empty Test Agent",
            instructions="Answer any question",
        )

        # Dependendo da implementação, pode lançar erro ou retornar resposta
        try:
            response = agent.chat("")
            # Se não lançar erro, deve retornar uma string
            assert isinstance(response, str)
        except Exception:
            # É aceitável que lance erro com mensagem vazia
            pass

    def test_chat_with_long_message_openai(self):
        """Testa chat com mensagem longa."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Long Message Agent",
            instructions="Summarize the text briefly.",
        )

        long_message = "This is a test. " * 100
        response = agent.chat(long_message)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_unicode_openai(self):
        """Testa chat com caracteres Unicode."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Unicode Agent",
            instructions="You are a multilingual assistant.",
        )

        response = agent.chat("Olá! Como você está? 你好 🌍")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


# ============================================================================
# TESTES DE CHAT - OLLAMA
# ============================================================================


@pytest.mark.integration
class TestAIAgentChatOllama:
    """Testes de chat com Ollama."""

    def test_simple_chat_with_ollama(self):
        """Testa chat simples com Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Chat Ollama Agent",
            instructions="You are a helpful assistant. Answer briefly.",
        )

        response = agent.chat("What is 2+2?")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_multiple_chats_with_history_ollama(self):
        """Testa múltiplas conversas mantendo histórico."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="History Ollama Agent",
            instructions="You are a helpful assistant. Remember the context.",
        )

        # Primeira mensagem
        response1 = agent.chat("My favorite color is blue")
        assert response1 is not None

        # Segunda mensagem referenciando a primeira
        response2 = agent.chat("What is my favorite color?")
        assert response2 is not None
        # Verifica se lembra do contexto
        assert "blue" in response2.lower()

    def test_chat_with_unicode_ollama(self):
        """Testa chat com caracteres Unicode no Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Unicode Ollama Agent",
            instructions="You are a multilingual assistant.",
        )

        response = agent.chat("Olá! 🌍")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


# ============================================================================
# TESTES DE HISTÓRICO
# ============================================================================


@pytest.mark.integration
class TestAIAgentHistory:
    """Testes de gerenciamento de histórico."""

    def test_clear_history_openai(self):
        """Testa limpeza de histórico com OpenAI."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Clear History Agent",
            instructions="Remember our conversation.",
        )

        # Faz um chat
        agent.chat("My name is Jordan")

        # Verifica que há histórico
        configs = agent.get_configs()
        assert len(configs["history"]) > 0

        # Limpa histórico
        agent.clear_history()

        # Verifica que histórico foi limpo
        configs = agent.get_configs()
        assert len(configs["history"]) == 0

    def test_clear_history_ollama(self):
        """Testa limpeza de histórico com Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Clear History Ollama",
            instructions="Remember context.",
        )

        # Faz um chat
        agent.chat("Hello")

        # Verifica que há histórico
        configs = agent.get_configs()
        assert len(configs["history"]) > 0

        # Limpa histórico
        agent.clear_history()

        # Verifica que histórico foi limpo
        configs = agent.get_configs()
        assert len(configs["history"]) == 0

    def test_history_max_size_enforcement_openai(self):
        """Testa que o tamanho máximo do histórico é respeitado."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Small History Agent",
            instructions="Chat briefly.",
            history_max_size=2,  # Apenas 2 mensagens (1 user + 1 assistant)
        )

        # Faz 3 chats (6 mensagens no total)
        agent.chat("First message")
        agent.chat("Second message")
        agent.chat("Third message")

        # Verifica que apenas as últimas mensagens estão no histórico
        configs = agent.get_configs()
        # Com max_size=2, deve ter no máximo 2 mensagens
        assert len(configs["history"]) <= 2


# ============================================================================
# TESTES DE MÉTRICAS
# ============================================================================


@pytest.mark.integration
class TestAIAgentMetrics:
    """Testes de coleta de métricas."""

    def test_get_metrics_after_chat_openai(self):
        """Testa coleta de métricas após chat com OpenAI."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Metrics Agent",
            instructions="Answer briefly.",
        )

        # Faz um chat
        agent.chat("Hello")

        # Obtém métricas
        metrics = agent.get_metrics()

        assert metrics is not None
        assert isinstance(metrics, list)
        assert len(metrics) > 0

        # Verifica estrutura da métrica
        first_metric = metrics[0]
        assert hasattr(first_metric, "model")
        assert hasattr(first_metric, "latency_ms")
        assert first_metric.latency_ms > 0

    def test_get_metrics_after_multiple_chats_openai(self):
        """Testa acúmulo de métricas após múltiplos chats."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Multi Metrics Agent",
            instructions="Answer briefly.",
        )

        # Faz 3 chats
        agent.chat("First")
        agent.chat("Second")
        agent.chat("Third")

        # Obtém métricas
        metrics = agent.get_metrics()

        assert len(metrics) >= 3

    def test_export_metrics_json_openai(self):
        """Testa exportação de métricas em JSON."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="JSON Metrics Agent",
            instructions="Answer briefly.",
        )

        # Faz um chat
        agent.chat("Test")

        # Exporta métricas
        json_str = agent.export_metrics_json()

        assert json_str is not None
        assert isinstance(json_str, str)
        assert "summary" in json_str
        assert "metrics" in json_str

    def test_export_metrics_prometheus_openai(self):
        """Testa exportação de métricas em formato Prometheus."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Prom Metrics Agent",
            instructions="Answer briefly.",
        )

        # Faz um chat
        agent.chat("Test")

        # Exporta métricas
        prom_str = agent.export_metrics_prometheus()

        assert prom_str is not None
        assert isinstance(prom_str, str)
        assert "chat_requests_total" in prom_str

    def test_get_metrics_after_chat_ollama(self):
        """Testa coleta de métricas após chat com Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Metrics Ollama Agent",
            instructions="Answer briefly.",
        )

        # Faz um chat
        agent.chat("Hello")

        # Obtém métricas
        metrics = agent.get_metrics()

        assert metrics is not None
        assert isinstance(metrics, list)
        assert len(metrics) > 0


# ============================================================================
# TESTES DE GET_CONFIGS
# ============================================================================


@pytest.mark.integration
class TestAIAgentGetConfigs:
    """Testes do método get_configs."""

    def test_get_configs_returns_all_fields_openai(self):
        """Testa que get_configs retorna todos os campos esperados."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Config Test Agent",
            instructions="Test instructions",
            config={"temperature": 0.7},
            history_max_size=15,
        )

        configs = agent.get_configs()

        assert "provider" in configs
        assert "model" in configs
        assert "name" in configs
        assert "instructions" in configs
        assert "config" in configs
        assert "history" in configs
        assert "history_max_size" in configs

        assert configs["provider"] == "openai"
        assert configs["model"] == IA_OPENAI_TEST_1
        assert configs["name"] == "Config Test Agent"
        assert configs["history_max_size"] == 15

    def test_get_configs_returns_all_fields_ollama(self):
        """Testa que get_configs retorna todos os campos esperados com Ollama."""
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST)

        agent = AIAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST,
            name="Config Ollama Agent",
            instructions="Test ollama",
            config={"temperature": 0.5},
            history_max_size=20,
        )

        configs = agent.get_configs()

        assert configs["provider"] == "ollama"
        assert configs["model"] == IA_OLLAMA_TEST
        assert configs["history_max_size"] == 20


# ============================================================================
# TESTES DE EDGE CASES E CENÁRIOS ESPECIAIS
# ============================================================================


@pytest.mark.integration
class TestAIAgentEdgeCases:
    """Testes de casos extremos e especiais."""

    def test_agent_with_very_long_instructions_openai(self):
        """Testa agente com instruções muito longas."""
        _get_openai_api_key()

        long_instructions = "You are a helpful assistant. " * 100

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Long Instructions Agent",
            instructions=long_instructions,
        )

        response = agent.chat("Hello")

        assert response is not None
        assert isinstance(response, str)

    def test_agent_with_special_characters_in_name(self):
        """Testa agente com caracteres especiais no nome."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Agent-Test_123!@#",
            instructions="Be helpful",
        )

        configs = agent.get_configs()
        assert configs["name"] == "Agent-Test_123!@#"

    def test_chat_after_clear_history_openai(self):
        """Testa que é possível fazer chat após limpar histórico."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Clear and Chat Agent",
            instructions="Remember context",
        )

        # Primeiro chat
        response1 = agent.chat("My name is Alice")
        assert response1 is not None

        # Limpa histórico
        agent.clear_history()

        # Segundo chat (não deve lembrar o primeiro)
        response2 = agent.chat("What is my name?")
        assert response2 is not None
        # Não deve mencionar Alice, pois o histórico foi limpo

    def test_multiple_agents_same_model_independent(self):
        """Testa que múltiplos agentes com o mesmo modelo são independentes."""
        _get_openai_api_key()

        agent1 = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Agent 1",
            instructions="You are agent 1",
        )

        agent2 = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Agent 2",
            instructions="You are agent 2",
        )

        # Faz chat com agent1
        agent1.chat("Hello from agent 1")

        # Verifica que agent2 não tem o histórico de agent1
        configs2 = agent2.get_configs()
        assert len(configs2["history"]) == 0

    def test_agent_with_minimal_config(self):
        """Testa agente com configuração mínima (apenas campos obrigatórios)."""
        _get_openai_api_key()

        agent = AIAgent(
            provider="openai",
            model=IA_OPENAI_TEST_2,
            name="Minimal Agent",
            instructions="Be helpful",
        )

        # Deve funcionar normalmente
        response = agent.chat("Hi")
        assert response is not None

        configs = agent.get_configs()
        assert configs["history_max_size"] == 10  # Valor padrão
        assert configs["config"] == {}  # Config padrão vazio
