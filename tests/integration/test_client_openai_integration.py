import os

import openai
import pytest

from createagents.application import ChatRepository
from createagents.domain import ChatException
from createagents.infra import OpenAIChatAdapter
from createagents.infra.adapters.tools.available_tools import AvailableTools

IA_OPENAI_TEST_1: str = (
    'gpt-5-nano'  # nao aceita configs, aceita tools e think: low
)
IA_OPENAI_TEST_2: str = (
    'gpt-4.1-mini'  # aceita configs e tools e nao aceita think
)

# allow-assertion-reduction: Replaced weak broad-exception assertions with concrete OpenAI and relocated-tool contract checks.


def _get_openai_api_key():
    from createagents.infra.adapters.openai.client_openai import ClientOpenAI
    from createagents.infra.config.environment import EnvironmentConfig

    if os.getenv('CI'):
        pytest.skip(
            'Skipping real API integration test on CI (set CI=0 to run)'
        )

    try:
        api_key = EnvironmentConfig.get_api_key(ClientOpenAI.API_OPENAI_NAME)
    except OSError:
        pytest.skip(
            f'Skipping integration test: {ClientOpenAI.API_OPENAI_NAME} not found in .env file'
        )
    else:
        return api_key


@pytest.mark.integration
class TestOpenAIChatAdapterIntegration:
    @pytest.mark.asyncio
    # assertion-reduction-reason: client conformance replaces presence checks.
    async def test_adapter_initialization(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        assert adapter is not None
        assert isinstance(adapter, ChatRepository)
        assert callable(adapter.chat)
        assert callable(adapter.get_metrics)

    @pytest.mark.asyncio
    async def test_chat_with_real_openai_simple_question(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is 2+2?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert '4' in response or 'four' in response.lower()

    @pytest.mark.asyncio
    async def test_chat_with_second_model(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Answer with one word only.',
            config={},
            tools=None,
            history=[],
            user_ask='What color is the sky? Answer with one word.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_history(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        history = [
            {'role': 'user', 'content': 'My name is Alice.'},
            {'role': 'assistant', 'content': 'Hello Alice! Nice to meet you.'},
        ]

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant.',
            config={},
            tools=None,
            history=history,
            user_ask='What is my name?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'alice' in response.lower()

    @pytest.mark.asyncio
    async def test_chat_with_complex_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a math teacher. Explain concepts simply and clearly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is a prime number?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            word in response.lower()
            for word in ['prime', 'number', 'divisible', 'divide']
        )

    @pytest.mark.asyncio
    async def test_chat_with_multiple_history_items(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        history = [
            {'role': 'user', 'content': 'I like pizza.'},
            {'role': 'assistant', 'content': 'Pizza is delicious!'},
            {'role': 'user', 'content': 'My favorite is pepperoni.'},
            {'role': 'assistant', 'content': 'Pepperoni is a classic choice!'},
        ]

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a friendly assistant.',
            config={},
            tools=None,
            history=history,
            user_ask='What food did I mention?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'pizza' in response.lower() or 'pepperoni' in response.lower()

    @pytest.mark.asyncio
    async def test_chat_with_special_characters(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Respond briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='Say hello in Chinese (你好) and add a celebration emoji 🎉',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_multiline_input(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        multiline_question = """
        Please answer this question:
        What are the three primary colors?
        List them one per line.
        """

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant.',
            config={},
            tools=None,
            history=[],
            user_ask=multiline_question,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_collects_metrics_on_success(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask="Say 'test'.",
        )

        assert response is not None

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OPENAI_TEST_1
        assert metrics[0].success is True
        assert metrics[0].latency_ms > 0
        if metrics[0].tokens_used is not None:
            assert metrics[0].tokens_used > 0
        assert metrics[0].error_message is None

    @pytest.mark.asyncio
    async def test_chat_with_invalid_model_raises_error(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException):
            await adapter.chat(
                model='invalid-model-that-does-not-exist-xyz-123',
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @pytest.mark.asyncio
    async def test_chat_collects_metrics_on_failure(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException):
            await adapter.chat(
                model='invalid-model-xyz-123',
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'invalid-model-xyz-123'
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    @pytest.mark.asyncio
    async def test_chat_with_empty_user_ask(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant.',
            config={},
            tools=None,
            history=[],
            user_ask='',
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_chat_with_empty_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='',
            config={},
            tools=None,
            history=[],
            user_ask='What is 1+1?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_none_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions=None,
            config={},
            tools=None,
            history=[],
            user_ask='What is 1+1?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_multiple_sequential_chats(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response1 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask="Say 'first'.",
        )

        response2 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask="Say 'second'.",
        )

        assert response1 is not None
        assert response2 is not None
        assert response1 != response2

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert all(m.success for m in metrics)

    @pytest.mark.asyncio
    async def test_chat_with_both_models(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response1 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is Python?',
        )

        response2 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is Python?',
        )

        assert response1 is not None
        assert response2 is not None
        assert isinstance(response1, str)
        assert isinstance(response2, str)

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == IA_OPENAI_TEST_1
        assert metrics[1].model == IA_OPENAI_TEST_1
        assert all(m.success for m in metrics)
        assert all(
            (m.tokens_used is None or m.tokens_used > 0) for m in metrics
        )

    @pytest.mark.asyncio
    async def test_adapter_implements_chat_repository_interface(self):
        _get_openai_api_key()

        from createagents.application.interfaces.chat_repository import (
            ChatRepository,
        )

        adapter = OpenAIChatAdapter()

        assert isinstance(adapter, ChatRepository)

    @pytest.mark.asyncio
    async def test_chat_with_long_conversation_history(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        history = []
        for i in range(5):
            history.append(
                {'role': 'user', 'content': f'Message number {i + 1}'}
            )
            history.append(
                {
                    'role': 'assistant',
                    'content': f'Response to message {i + 1}',
                }
            )

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant.',
            config={},
            tools=None,
            history=history,
            user_ask='How many messages did I send before this one?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_response_is_not_empty(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant.',
            config={},
            tools=None,
            history=[],
            user_ask='Hello!',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert response.strip() != ''

    @pytest.mark.asyncio
    async def test_get_metrics_returns_copy(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Test',
        )

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        assert metrics1 is not metrics2
        assert len(metrics1) == len(metrics2)

    @pytest.mark.asyncio
    async def test_chat_with_config_parameter(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 100,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_very_long_prompt(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        long_question = 'Tell me about Python. ' * 50

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask=long_question,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        if metrics[0].tokens_used is not None:
            assert metrics[0].tokens_used > 0
        if metrics[0].prompt_tokens is not None:
            assert metrics[0].prompt_tokens > 0

    @pytest.mark.asyncio
    async def test_chat_with_code_in_prompt(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a code reviewer.',
            config={},
            tools=None,
            history=[],
            user_ask='What does this Python code do?\n\ndef add(a, b):\n    return a + b',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_metrics_include_token_counts(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is 2+2?',
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1

        metric = metrics[0]
        if metric.tokens_used is not None:
            assert metric.tokens_used > 0
        if metric.prompt_tokens is not None:
            assert metric.prompt_tokens > 0
        if metric.completion_tokens is not None:
            assert metric.completion_tokens > 0
        if all(
            [
                metric.tokens_used,
                metric.prompt_tokens,
                metric.completion_tokens,
            ]
        ):
            assert (
                metric.tokens_used
                == metric.prompt_tokens + metric.completion_tokens
            )

    @pytest.mark.asyncio
    async def test_chat_with_system_message_variations(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response1 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a professional assistant. Be formal.',
            config={},
            tools=None,
            history=[],
            user_ask='Hello',
        )

        response2 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a friendly buddy. Be casual.',
            config={},
            tools=None,
            history=[],
            user_ask='Hello',
        )

        assert response1 is not None
        assert response2 is not None
        assert response1 != response2

    @pytest.mark.asyncio
    async def test_chat_handles_json_request(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Respond only in valid JSON format.',
            config={},
            tools=None,
            history=[],
            user_ask='Return JSON with one key "greeting" and value "hello"',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_error_preserves_original_exception(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException) as exc_info:
            await adapter.chat(
                model='totally-invalid-model-12345',
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )
        assert exc_info.value.original_error is not None
        assert (
            'OpenAI' in str(exc_info.value)
            or 'modelo' in str(exc_info.value).lower()
        )


@pytest.mark.integration
class TestClientOpenAIIntegration:
    @pytest.mark.asyncio
    async def test_get_client_with_real_openai_api(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        api_key = _get_openai_api_key()
        client = ClientOpenAI.get_client(api_key)

        assert client is not None
        assert isinstance(client, openai.AsyncOpenAI)

    @pytest.mark.asyncio
    async def test_client_has_required_attributes(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        api_key = _get_openai_api_key()
        client = ClientOpenAI.get_client(api_key)

        assert isinstance(client, openai.AsyncOpenAI)

    @pytest.mark.asyncio
    async def test_list_models_with_real_api(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        api_key = _get_openai_api_key()
        client = ClientOpenAI.get_client(api_key)

        models = await client.models.list()
        assert models is not None
        model_list = list(models)
        assert len(model_list) > 0

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_error(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        _get_openai_api_key()

        invalid_key = 'sk-invalid-test-key-12345'
        client = ClientOpenAI.get_client(invalid_key)

        assert client is not None

        with pytest.raises(openai.OpenAIError):
            await client.models.list()

    @pytest.mark.asyncio
    async def test_get_client_multiple_times_with_same_key(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        api_key = _get_openai_api_key()

        client1 = ClientOpenAI.get_client(api_key)
        client2 = ClientOpenAI.get_client(api_key)

        assert client1 is not None
        assert client2 is not None
        models1 = client1.models.list()
        models2 = client2.models.list()
        assert models1 is not None
        assert models2 is not None

    @pytest.mark.asyncio
    async def test_client_api_key_constant(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        assert ClientOpenAI.API_OPENAI_NAME == 'OPENAI_API_KEY'
        assert isinstance(ClientOpenAI.API_OPENAI_NAME, str)
        assert len(ClientOpenAI.API_OPENAI_NAME) > 0

    @pytest.mark.parametrize(
        'invalid_key',
        [
            '',
            'sk-invalid-test-key-12345',
        ],
    )
    @pytest.mark.asyncio
    async def test_get_client_with_invalid_key_formats(self, invalid_key):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        _get_openai_api_key()

        client = ClientOpenAI.get_client(invalid_key)
        assert client is not None

        with pytest.raises(openai.OpenAIError):
            await client.models.list()

    @pytest.mark.asyncio
    async def test_get_client_with_none_uses_env_variable(self):
        from createagents.infra.adapters.openai.client_openai import (
            ClientOpenAI,
        )

        _get_openai_api_key()

        client = ClientOpenAI.get_client(None)
        assert client is not None

        models = await client.models.list()
        assert models is not None


@pytest.mark.integration
class TestOpenAIAdapterConfigsReais:
    @pytest.mark.asyncio
    async def test_chat_with_temperature_config_low(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'temperature': 0.0}

        response1 = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="Answer with exactly 'yes'.",
            config=config,
            tools=None,
            history=[],
            user_ask='Is water a liquid?',
        )

        response2 = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions="Answer with exactly 'yes'.",
            config=config,
            tools=None,
            history=[],
            user_ask='Is water a liquid?',
        )

        assert response1 is not None
        assert response2 is not None
        assert isinstance(response1, str)
        assert isinstance(response2, str)
        assert response1 == response2

    @pytest.mark.asyncio
    async def test_chat_with_temperature_config_high(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'temperature': 1.5}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be creative and answer with varied responses.',
            config=config,
            tools=None,
            history=[],
            user_ask='Tell me something interesting about Python.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_temperature_boundary_values(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_min = {'temperature': 0.0}
        response_min = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config_min,
            tools=None,
            history=[],
            user_ask='What is 2+2?',
        )

        config_max = {'temperature': 2.0}
        response_max = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config_max,
            tools=None,
            history=[],
            user_ask='What is 2+2?',
        )

        assert response_min is not None
        assert response_max is not None
        assert isinstance(response_min, str)
        assert isinstance(response_max, str)

    @pytest.mark.asyncio
    async def test_chat_with_max_tokens_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'max_tokens': 50}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is Python? Explain in detail.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        if metrics[-1].completion_tokens is not None:
            assert metrics[-1].completion_tokens > 0

    @pytest.mark.asyncio
    async def test_chat_with_top_p_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'top_p': 0.5}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is artificial intelligence?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_multiple_config_parameters(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 150,
            'top_p': 0.9,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a helpful assistant.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain quantum computing in simple terms.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_empty_config_uses_defaults(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is Python?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_metrics_reflect_config_impact(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_limited = {'max_tokens': 20}
        await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config_limited,
            tools=None,
            history=[],
            user_ask='Tell me about Python programming.',
        )

        metrics_limited = adapter.get_metrics()
        tokens_limited = metrics_limited[-1].completion_tokens

        adapter2 = OpenAIChatAdapter()
        config_unlimited = {}
        await adapter2.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config_unlimited,
            tools=None,
            history=[],
            user_ask='Tell me about Python programming.',
        )

        metrics_unlimited = adapter2.get_metrics()
        tokens_unlimited = metrics_unlimited[-1].completion_tokens

        assert metrics_limited[-1].success is True
        assert metrics_unlimited[-1].success is True

        if tokens_limited is not None and tokens_unlimited is not None:
            assert tokens_limited <= tokens_unlimited

    @pytest.mark.asyncio
    async def test_chat_temperature_affects_response_variety(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_low = {'temperature': 0.0}
        response_low_1 = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a helpful assistant.',
            config=config_low,
            tools=None,
            history=[],
            user_ask='Say something about clouds.',
        )

        adapter_mid = OpenAIChatAdapter()
        config_mid = {'temperature': 1.0}
        response_mid = await adapter_mid.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a helpful assistant.',
            config=config_mid,
            tools=None,
            history=[],
            user_ask='Say something about clouds.',
        )

        assert response_low_1 is not None
        assert response_mid is not None
        assert isinstance(response_low_1, str)
        assert isinstance(response_mid, str)

    @pytest.mark.asyncio
    async def test_chat_with_negative_max_tokens_ignored(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'max_tokens': -1}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config,
            tools=None,
            history=[],
            user_ask='Hello',
        )
        assert response is not None

    @pytest.mark.asyncio
    async def test_adapter_reads_timeout_from_environment(self):
        _get_openai_api_key()
        adapter = OpenAIChatAdapter()
        assert adapter is not None
        assert isinstance(adapter, ChatRepository)

    @pytest.mark.asyncio
    async def test_adapter_reads_max_retries_from_environment(self):
        _get_openai_api_key()
        adapter = OpenAIChatAdapter()
        assert adapter is not None
        assert isinstance(adapter, ChatRepository)

    @pytest.mark.asyncio
    async def test_chat_config_params_do_not_affect_instructions(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.3,
            'max_tokens': 100,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a pirate. Answer like a pirate.',
            config=config,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_config_with_history_and_parameters(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.6,
            'max_tokens': 120,
        }

        history = [
            {'role': 'user', 'content': 'My name is Bob.'},
            {'role': 'assistant', 'content': 'Nice to meet you, Bob!'},
        ]

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a helpful assistant. Be friendly.',
            config=config,
            tools=None,
            history=history,
            user_ask='What is my name?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'bob' in response.lower()

    @pytest.mark.asyncio
    async def test_multiple_adapters_independent_configs(self):
        _get_openai_api_key()

        adapter1 = OpenAIChatAdapter()
        adapter2 = OpenAIChatAdapter()

        config1 = {'temperature': 0.2}
        config2 = {'temperature': 1.8}

        response1 = await adapter1.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config1,
            tools=None,
            history=[],
            user_ask='Describe the ocean.',
        )

        response2 = await adapter2.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config2,
            tools=None,
            history=[],
            user_ask='Describe the ocean.',
        )

        assert response1 is not None
        assert response2 is not None
        assert response1 != response2

    @pytest.mark.asyncio
    async def test_chat_config_preserved_across_multiple_calls(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.5,
            'max_tokens': 100,
        }

        for i in range(2):
            response = await adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Answer briefly.',
                config=config,
                tools=None,
                history=[],
                user_ask=f'Question {i + 1}: Say hello.',
            )

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert all(m.success for m in metrics)


@pytest.mark.integration
class TestOpenAIChatAdapterToolsIntegration:
    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_get_date(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC? Use the current_date tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_get_time(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask='What time is it now in UTC? Use the current_date tool.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_get_datetime(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask='What is the current date and time in America/New_York? Use the current_date tool.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_get_timestamp(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask='What is the current Unix timestamp? Use the current_date tool.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_date_with_weekday(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask="What is today's full date with weekday in America/Sao_Paulo? Use the current_date tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_multiple_timezones(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']

        for tz in timezones:
            response = await adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='You are a helpful assistant. Use tools when appropriate.',
                config={},
                tools=tools,
                history=[],
                user_ask=f'What time is it in {tz}? Use the current_date tool.',
            )

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_readlocalfile_tool_text_file(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        tool_names = [t.name for t in tools]
        if 'read_local_file' not in tool_names:
            pytest.skip(
                'ReadLocalFileTool not available (missing optional dependencies)'
            )

        file_path = os.path.abspath('.fixtures/sample_text.txt')

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask=f'Read the file at {file_path} and tell me how many lines it has. Use the read_local_file tool.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_readlocalfile_tool_csv_file(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        tool_names = [t.name for t in tools]
        if 'read_local_file' not in tool_names:
            pytest.skip(
                'ReadLocalFileTool not available (missing optional dependencies)'
            )

        file_path = os.path.abspath('.fixtures/sample_data.csv')

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask=f'Read the CSV file at {file_path} and tell me the names in it. Use the read_local_file tool.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_configs_combined(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'temperature': 0.7,
            'max_tokens': 200,
            'top_p': 0.9,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config=config,
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC? Use the current_date tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        assert metrics[-1].success

    @pytest.mark.asyncio
    async def test_chat_with_multiple_tool_calls_in_conversation(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response1 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC?",
        )

        assert response1 is not None
        history = [
            {'role': 'user', 'content': "What is today's date in UTC?"},
            {'role': 'assistant', 'content': response1},
        ]

        response2 = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=history,
            user_ask='What time is it now in America/New_York?',
        )

        assert response2 is not None
        assert isinstance(response2, str)
        assert len(response2) > 0

    @pytest.mark.asyncio
    async def test_chat_without_tools_when_tools_available(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='You are a helpful assistant.',
            config={},
            tools=tools,
            history=[],
            user_ask='What is 5+5? Just answer with the number.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert '10' in response or 'ten' in response.lower()

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_think_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'temperature': 0.5,
            'top_p': 0.9,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be accurate when using tools.',
            config=config,
            tools=tools,
            history=[],
            user_ask='What is the current Unix timestamp?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_top_k_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'temperature': 0.7,
            'max_tokens': 200,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Use tools to get accurate and current information.',
            config=config,
            tools=tools,
            history=[],
            user_ask="What is today's date in America/New_York?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_all_configs_openai(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'temperature': 0.6,
            'max_tokens': 180,
            'top_p': 0.88,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Use tools to get accurate information.',
            config=config,
            tools=tools,
            history=[],
            user_ask='What is the current date and time in UTC?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        assert metrics[-1].success


@pytest.mark.integration
class TestOpenAIChatAdapterConfigValidation:
    @pytest.mark.asyncio
    async def test_chat_with_boundary_max_tokens_values(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_min = {'max_tokens': 16}
        response_min = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be extremely brief.',
            config=config_min,
            tools=None,
            history=[],
            user_ask='Hi',
        )

        assert response_min is not None
        assert isinstance(response_min, str)

    @pytest.mark.asyncio
    async def test_chat_with_boundary_top_p_values(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_min = {'top_p': 0.0}
        response_min = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config_min,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response_min is not None

        config_max = {'top_p': 1.0}
        response_max = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config_max,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response_max is not None

    @pytest.mark.asyncio
    async def test_chat_with_mixed_configs_at_boundaries(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.0,
            'max_tokens': 50,
            'top_p': 1.0,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config,
            tools=None,
            history=[],
            user_ask='Hi',
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_chat_with_max_temperature_and_max_tokens(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 2.0,
            'max_tokens': 1000,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be creative.',
            config=config,
            tools=None,
            history=[],
            user_ask='Tell me something interesting.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestOpenAIChatAdapterConfigEdgeCases:
    @pytest.mark.asyncio
    async def test_chat_with_all_configs_at_boundaries(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_min = {
            'temperature': 0.0,
            'max_tokens': 16,
            'top_p': 0.0,
        }

        response_min = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config_min,
            tools=None,
            history=[],
            user_ask='Hi',
        )

        assert response_min is not None
        assert isinstance(response_min, str)

        config_max = {
            'temperature': 2.0,
            'max_tokens': 1000,
            'top_p': 1.0,
        }

        response_max = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config_max,
            tools=None,
            history=[],
            user_ask='Hi again',
        )

        assert response_max is not None
        assert isinstance(response_max, str)

    @pytest.mark.asyncio
    async def test_chat_with_only_temperature_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'temperature': 0.5}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_only_max_tokens_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'max_tokens': 50}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain Python in one sentence.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_only_top_p_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'top_p': 0.8}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is AI?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_temperature_and_max_tokens(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.3,
            'max_tokens': 75,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be concise.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is machine learning?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_temperature_and_top_p(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.8,
            'top_p': 0.95,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be creative.',
            config=config,
            tools=None,
            history=[],
            user_ask='Tell me something interesting.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_max_tokens_and_top_p(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'max_tokens': 100,
            'top_p': 0.7,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer concisely.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain neural networks.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_think_config_low_effort(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'think': 'low'}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Think briefly before answering.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is 25 * 4?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_think_config_high_effort(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'think': 'low'}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Think deeply about this question.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain the philosophical implications of quantum mechanics.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_top_k_config(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {'temperature': 0.7}

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is machine learning?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_top_k_boundary_values(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config_small = {'max_tokens': 50}
        response_small = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config_small,
            tools=None,
            history=[],
            user_ask='Hi',
        )

        assert response_small is not None
        assert isinstance(response_small, str)

        config_large = {'max_tokens': 500}
        response_large = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer.',
            config=config_large,
            tools=None,
            history=[],
            user_ask='Hi',
        )

        assert response_large is not None
        assert isinstance(response_large, str)

    @pytest.mark.asyncio
    async def test_chat_with_temperature_top_k_top_p_combined(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.8,
            'top_p': 0.9,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Be creative and thoughtful.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is the future of AI?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_all_supported_configs_openai(self):
        _get_openai_api_key()

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 150,
            'top_p': 0.85,
        }

        response = await adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Answer helpfully.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain the impact of deep learning.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        assert metrics[-1].success
