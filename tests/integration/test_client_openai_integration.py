import os

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter

# Modelos para testes de integração
IA_OPENAI_TEST_1: str = "gpt-5-mini"
IA_OPENAI_TEST_2: str = "gpt-5-nano"


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


@pytest.mark.integration
class TestOpenAIChatAdapterIntegration:
    """Testes de integração para o OpenAIChatAdapter com a API real do OpenAI."""

    def test_adapter_initialization(self):
        """Testa inicialização do adapter com API key real."""
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        assert adapter is not None
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)
        assert hasattr(adapter, "get_metrics")
        assert callable(adapter.get_metrics)

    def test_chat_with_real_openai_simple_question(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="You are a helpful assistant. Answer with one word only.",
            config={},
            history=[],
            user_ask="What color is the sky? Answer with one word.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_history(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        history = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
        ]

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            history=history,
            user_ask="What is my name?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "alice" in response.lower()

    def test_chat_with_complex_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        history = [
            {"role": "user", "content": "I like pizza."},
            {"role": "assistant", "content": "Pizza is delicious!"},
            {"role": "user", "content": "My favorite is pepperoni."},
            {"role": "assistant", "content": "Pepperoni is a classic choice!"},
        ]

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="You are a helpful assistant. Respond briefly.",
            config={},
            history=[],
            user_ask="Say hello in Chinese (你好) and add a celebration emoji 🎉",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_multiline_input(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        multiline_question = """
        Please answer this question:
        What are the three primary colors?
        List them one per line.
        """

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="You are a helpful assistant.",
            config={},
            history=[],
            user_ask=multiline_question,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_collects_metrics_on_success(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="Say 'test'.",
        )

        assert response is not None

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OPENAI_TEST_1
        assert metrics[0].success is True
        assert metrics[0].latency_ms > 0
        assert metrics[0].tokens_used is not None
        assert metrics[0].tokens_used > 0
        assert metrics[0].prompt_tokens is not None
        assert metrics[0].completion_tokens is not None
        assert metrics[0].error_message is None

    def test_chat_with_invalid_model_raises_error(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException):
            adapter.chat(
                model="invalid-model-that-does-not-exist-xyz-123",
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )

    def test_chat_collects_metrics_on_failure(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            history=[],
            user_ask="",
        )

        assert response is not None
        assert isinstance(response, str)

    def test_chat_with_empty_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="",
            config={},
            history=[],
            user_ask="What is 1+1?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_none_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions=None,
            config={},
            history=[],
            user_ask="What is 1+1?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_multiple_sequential_chats(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response1 = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="Say 'first'.",
        )

        response2 = adapter.chat(
            model=IA_OPENAI_TEST_1,
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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response1 = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="What is Python?",
        )

        response2 = adapter.chat(
            model=IA_OPENAI_TEST_2,
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
        assert metrics[0].model == IA_OPENAI_TEST_1
        assert metrics[1].model == IA_OPENAI_TEST_2
        assert all(m.success for m in metrics)
        assert all(m.tokens_used is not None and m.tokens_used > 0 for m in metrics)

    def test_adapter_implements_chat_repository_interface(self):
        _get_openai_api_key()

        from src.application.interfaces.chat_repository import ChatRepository

        adapter = OpenAIChatAdapter()

        assert isinstance(adapter, ChatRepository)

    def test_chat_with_long_conversation_history(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        # Cria um histórico com várias mensagens
        history = []
        for i in range(5):
            history.append({"role": "user", "content": f"Message number {i+1}"})
            history.append(
                {"role": "assistant", "content": f"Response to message {i+1}"}
            )

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            history=history,
            user_ask="How many messages did I send before this one?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_response_is_not_empty(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
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
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            "temperature": 0.7,
            "max_tokens": 100,
        }

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="Answer briefly.",
            config=config,
            history=[],
            user_ask="Say hello.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_very_long_prompt(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        # Cria uma pergunta longa
        long_question = "Tell me about Python. " * 50

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask=long_question,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        # Verificar métricas de tokens
        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].tokens_used > 0
        assert metrics[0].prompt_tokens > 0

    def test_chat_with_code_in_prompt(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="You are a code reviewer.",
            config={},
            history=[],
            user_ask="What does this Python code do?\n\ndef add(a, b):\n    return a + b",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_metrics_include_token_counts(self):
        """Testa que as métricas incluem contagens de tokens detalhadas."""
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="Answer briefly.",
            config={},
            history=[],
            user_ask="What is 2+2?",
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1

        metric = metrics[0]
        assert metric.tokens_used is not None
        assert metric.tokens_used > 0
        assert metric.prompt_tokens is not None
        assert metric.prompt_tokens > 0
        assert metric.completion_tokens is not None
        assert metric.completion_tokens > 0
        # Total deve ser a soma de prompt + completion
        assert metric.tokens_used == metric.prompt_tokens + metric.completion_tokens

    def test_chat_with_system_message_variations(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        # Teste com instrução formal
        response1 = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="You are a professional assistant. Be formal.",
            config={},
            history=[],
            user_ask="Hello",
        )

        # Teste com instrução casual
        response2 = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions="You are a friendly buddy. Be casual.",
            config={},
            history=[],
            user_ask="Hello",
        )

        assert response1 is not None
        assert response2 is not None
        assert response1 != response2

    def test_chat_handles_json_request(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="You are a helpful assistant. Respond only in valid JSON format.",
            config={},
            history=[],
            user_ask='Return JSON with one key "greeting" and value "hello"',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_error_preserves_original_exception(self):
        """Testa que erros preservam a exceção original."""
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        try:
            adapter.chat(
                model="totally-invalid-model-12345",
                instructions="Test",
                config={},
                history=[],
                user_ask="Test",
            )
            assert False, "Deveria ter lançado ChatException"
        except ChatException as e:
            assert e.original_error is not None
            # Verificar que a mensagem contém informação útil
            assert "OpenAI" in str(e) or "modelo" in str(e).lower()


@pytest.mark.integration
class TestClientOpenAIIntegration:
    def test_get_client_with_real_openai_api(self):
        """Integration test: cria o client real do OpenAI se a chave estiver disponível."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        api_key = _get_openai_api_key()
        client = ClientOpenAI.get_client(api_key)

        assert client is not None
        assert hasattr(client, "chat")
        assert hasattr(client, "models")

    def test_client_has_required_attributes(self):
        """Valida que o cliente OpenAI possui os atributos necessários para chat."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        api_key = _get_openai_api_key()
        client = ClientOpenAI.get_client(api_key)

        # Verificar que os atributos principais existem
        assert hasattr(client, "chat"), "Client deve ter atributo 'chat'"
        assert hasattr(client, "models"), "Client deve ter atributo 'models'"

    def test_list_models_with_real_api(self):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        api_key = _get_openai_api_key()
        client = ClientOpenAI.get_client(api_key)

        try:
            models = client.models.list()
            assert models is not None
            # A resposta deve ser iterável
            model_list = list(models)
            assert len(model_list) > 0, "Deve haver pelo menos um modelo disponível"
        except Exception as exc:  # pragma: no cover - só executado em integração real
            pytest.fail(f"Real OpenAI API call to list models failed: {exc}")

    def test_invalid_api_key_raises_error(self):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        # Se a chave real não está disponível, pula este teste
        _get_openai_api_key()

        invalid_key = "sk-invalid-test-key-12345"
        client = ClientOpenAI.get_client(invalid_key)

        # O client é criado, mas a chamada deve falhar
        assert client is not None

        with pytest.raises(Exception):  # OpenAI lança AuthenticationError
            client.models.list()

    def test_get_client_multiple_times_with_same_key(self):
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        api_key = _get_openai_api_key()

        client1 = ClientOpenAI.get_client(api_key)
        client2 = ClientOpenAI.get_client(api_key)

        assert client1 is not None
        assert client2 is not None
        # Verificar que ambos conseguem chamar a API
        try:
            models1 = client1.models.list()
            models2 = client2.models.list()
            assert models1 is not None
            assert models2 is not None
        except Exception as exc:  # pragma: no cover
            pytest.fail(f"Multiple client calls failed: {exc}")

    def test_client_api_key_constant(self):
        """Valida que a constante API_OPENAI_NAME está definida corretamente."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert hasattr(ClientOpenAI, "API_OPENAI_NAME")
        assert ClientOpenAI.API_OPENAI_NAME == "OPENAI_API_KEY"
        assert isinstance(ClientOpenAI.API_OPENAI_NAME, str)
        assert len(ClientOpenAI.API_OPENAI_NAME) > 0

    @pytest.mark.parametrize(
        "invalid_key",
        [
            "",
            "sk-invalid-test-key-12345",
        ],
    )
    def test_get_client_with_invalid_key_formats(self, invalid_key):
        """Testa comportamento com chaves em formato inválido."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        # _get_openai_api_key() já faz skip se não houver chave real
        _get_openai_api_key()

        # Criar client com chave inválida (não deve lançar erro imediato)
        client = ClientOpenAI.get_client(invalid_key)
        assert client is not None

        # Mas chamadas devem falhar
        with pytest.raises(Exception):  # pragma: no cover
            client.models.list()

    def test_get_client_with_none_uses_env_variable(self):
        """Testa que passar None permite que o cliente use a variável de ambiente."""
        from src.infra.adapters.OpenAI.client_openai import ClientOpenAI

        # Garantir que a chave real está disponível
        _get_openai_api_key()

        # Quando passamos None, o OpenAI client usa OPENAI_API_KEY do ambiente
        client = ClientOpenAI.get_client(None)
        assert client is not None

        # Deve funcionar corretamente
        try:
            models = client.models.list()
            assert models is not None
        except Exception as exc:  # pragma: no cover
            pytest.fail(f"Client with None should use env var, but failed: {exc}")
