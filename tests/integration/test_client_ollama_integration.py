import os

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter

# Modelos para testes de integração
IA_OLLAMA_TEST_1: str = "phi4-mini:latest"  # A IA DEVE ESTAR BAIXADA
IA_OLLAMA_TEST_2: str = "gemma3:4b"  # A IA DEVE ESTAR BAIXADA


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


def _check_model_available(model: str):
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


@pytest.fixture(scope="session", autouse=True)
def teardown_ollama_models():
    """Teardown session-scoped: tenta parar/descarregar os modelos usados nos testes ao final.

    A fixture é automática para os testes de integração e só tenta executar o comando
    `ollama stop <model>` quando a ferramenta `ollama` estiver disponível e não
    estivermos rodando em CI (onde testes reais são normalmente pulados).
    """
    # Setup: nada a fazer antes dos testes
    yield

    import subprocess
    import os

    # Não executar em CI
    if os.getenv("CI"):
        return

    # Modelos que utilizamos nos testes
    models = [IA_OLLAMA_TEST_1, IA_OLLAMA_TEST_2]

    # Verifica se o CLI está disponível
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=3)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return

    for m in models:
        try:
            # Tenta parar o modelo se o comando 'ollama stop' for suportado
            subprocess.run(["ollama", "stop", m], capture_output=True, timeout=10)
        except Exception:
            # Ignorar qualquer erro no teardown para não falhar a suíte
            continue


@pytest.mark.integration
class TestOllamaChatAdapterIntegration:
    """Testes de integração para o OllamaChatAdapter com o Ollama real."""

    def test_adapter_initialization(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        assert adapter is not None
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)
        assert hasattr(adapter, "get_metrics")
        assert callable(adapter.get_metrics)

    def test_chat_with_real_ollama_simple_question(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Answer briefly.",
            config={},
            history=[],
            user_ask="What is 2+2?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response or "four" in response.lower()

    def test_chat_with_second_model(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a helpful assistant. Answer with one word only.",
            config={},
            history=[],
            user_ask="What color is the sky? Answer with one word.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_history(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
        ]

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            history=history,
            user_ask="What is my name?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        # A resposta deve mencionar Alice
        assert "alice" in response.lower()

    def test_chat_with_complex_instructions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a math teacher. Explain concepts simply and clearly.",
            config={},
            history=[],
            user_ask="What is a prime number?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            word in response.lower()
            for word in ["prime", "number", "divisible", "divide"]
        )

    def test_chat_with_multiple_history_items(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "I like pizza."},
            {"role": "assistant", "content": "Pizza is delicious!"},
            {"role": "user", "content": "My favorite is pepperoni."},
            {"role": "assistant", "content": "Pepperoni is a classic choice!"},
        ]

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a friendly assistant.",
            config={},
            history=history,
            user_ask="What food did I mention?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "pizza" in response.lower()

    def test_chat_with_special_characters(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Respond briefly.",
            config={},
            history=[],
            user_ask="Say hello in Chinese (你好) and add a celebration emoji 🎉",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_multiline_input(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        multiline_question = """
        Please answer this question:
        What are the three primary colors?
        List them one per line.
        """

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a helpful assistant.",
            config={},
            history=[],
            user_ask=multiline_question,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_collects_metrics_on_success(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="Say 'test'.",
        )

        assert response is not None

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[0].success is True
        assert metrics[0].latency_ms > 0
        assert metrics[0].error_message is None

    def test_chat_with_invalid_model_raises_error(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException):
            adapter.chat(
                model="invalid-model-that-does-not-exist",
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    def test_chat_collects_metrics_on_failure(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model="invalid-model-xyz-123",
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == "invalid-model-xyz-123"
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    def test_chat_with_empty_user_ask(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            history=[],
            user_ask="",
        )

        # O Ollama deve responder mesmo com entrada vazia
        assert response is not None
        assert isinstance(response, str)

    def test_chat_with_empty_instructions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="",
            config={},
            history=[],
            user_ask="What is 1+1?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_none_instructions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions=None,
            config={},
            history=[],
            user_ask="What is 1+1?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_multiple_sequential_chats(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response1 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="Say 'first'.",
        )

        response2 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="Say 'second'.",
        )

        assert response1 is not None
        assert response2 is not None
        assert response1 != response2

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert all(m.success for m in metrics)

    def test_chat_with_both_models(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response1 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="What is Python?",
        )

        response2 = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="What is Python?",
        )

        assert response1 is not None
        assert response2 is not None
        assert isinstance(response1, str)
        assert isinstance(response2, str)

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[1].model == IA_OLLAMA_TEST_2
        assert all(m.success for m in metrics)

    def test_adapter_implements_chat_repository_interface(self):
        """Verifica que o adapter implementa a interface ChatRepository."""
        _check_ollama_available()

        from src.application.interfaces.chat_repository import ChatRepository

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)

    def test_chat_with_long_conversation_history(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        # Cria um histórico com várias mensagens
        history = []
        for i in range(5):
            history.append({"role": "user", "content": f"Message number {i+1}"})
            history.append(
                {"role": "assistant", "content": f"Response to message {i+1}"}
            )

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            history=history,
            user_ask="How many messages did I send before this one?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_response_is_not_empty(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a helpful assistant.",
            config={},
            history=[],
            user_ask="Hello!",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert response.strip() != ""

    def test_get_metrics_returns_copy(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            history=[],
            user_ask="Test",
        )

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        # As listas devem ser diferentes objetos
        assert metrics1 is not metrics2
        # Mas com o mesmo conteúdo
        assert len(metrics1) == len(metrics2)

    def test_chat_with_config_parameter(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            "temperature": 0.7,
            "max_tokens": 100,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config=config,
            history=[],
            user_ask="Say hello.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
