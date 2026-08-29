import contextlib
import os
from collections.abc import Generator

import pytest

from createagents.application import ChatRepository
from createagents.domain import ChatException
from createagents.infra import OllamaChatAdapter

IA_OLLAMA_TEST_1: str = 'granite4:latest'  # aceita tools, configs e não think
IA_OLLAMA_TEST_2: str = (
    'gpt-oss:120b-cloud'  # não aceita tools, aceita configs e think true
)


def _check_ollama_available() -> None:
    # Integration-only probe for an optional local Ollama installation.
    import subprocess  # nosec B404

    if os.getenv('CI'):
        pytest.skip(
            'Skipping real Ollama integration test on CI (set CI=0 to run)'
        )

    try:
        result = subprocess.run(  # nosec B603, B607
            ['ollama', 'list'], capture_output=True, timeout=5
        )
        if result.returncode != 0:
            pytest.skip('Ollama is not available or not running')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip('Ollama is not installed or not responding')


def _check_model_available(model: str) -> None:
    # Integration-only probe for an optional local Ollama installation.
    import subprocess  # nosec B404

    try:
        result = subprocess.run(  # nosec B603, B607
            ['ollama', 'list'], capture_output=True, text=True, timeout=5
        )
        if model not in result.stdout:
            pytest.skip(
                f'Model {model} is not available in Ollama. Run: ollama pull {model}'
            )
    except (OSError, subprocess.SubprocessError) as error:
        pytest.skip(
            f'Could not verify available models: {type(error).__name__}'
        )


@pytest.fixture(scope='session', autouse=True)
def teardown_ollama_models() -> Generator[None, None, None]:
    yield

    import subprocess  # nosec B404

    if os.getenv('CI'):
        return

    models = [IA_OLLAMA_TEST_1, IA_OLLAMA_TEST_2]

    with contextlib.suppress(FileNotFoundError, subprocess.TimeoutExpired):
        subprocess.run(  # nosec B603, B607
            ['ollama', '--version'], capture_output=True, timeout=3
        )

    for m in models:
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            subprocess.run(  # nosec B603, B607
                ['ollama', 'stop', m], capture_output=True, timeout=10
            )


@pytest.mark.integration
class TestOllamaChatAdapterIntegration:
    # assertion-reduction-reason: interface conformance replaces presence checks.
    def test_adapter_initialization(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        assert adapter is not None
        assert isinstance(adapter, ChatRepository)
        assert callable(adapter.chat)
        assert callable(adapter.get_metrics)

    @pytest.mark.asyncio
    async def test_chat_with_real_ollama_simple_question(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = [
            {'role': 'user', 'content': 'My name is Alice.'},
            {'role': 'assistant', 'content': 'Hello Alice! Nice to meet you.'},
        ]

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = [
            {'role': 'user', 'content': 'I like pizza.'},
            {'role': 'assistant', 'content': 'Pizza is delicious!'},
            {'role': 'user', 'content': 'My favorite is pepperoni.'},
            {'role': 'assistant', 'content': 'Pepperoni is a classic choice!'},
        ]

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='You are a friendly assistant.',
            config={},
            tools=None,
            history=history,
            user_ask='What food did I mention?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'pizza' in response.lower()

    @pytest.mark.asyncio
    async def test_chat_with_special_characters(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        multiline_question = """
        Please answer this question:
        What are the three primary colors?
        List them one per line.
        """

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
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

    @pytest.mark.asyncio
    async def test_chat_with_invalid_model_raises_error(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException):
            await adapter.chat(
                model='invalid-model-that-does-not-exist',
                instructions='Test',
                config={},
                tools=None,
                history=[],
                user_ask='Test',
            )

    @pytest.mark.asyncio
    async def test_chat_collects_metrics_on_failure(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response1 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask="Say 'first'.",
        )

        response2 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response1 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config={},
            tools=None,
            history=[],
            user_ask='What is Python?',
        )

        response2 = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[1].model == IA_OLLAMA_TEST_2
        assert all(m.success for m in metrics)

    def test_adapter_implements_chat_repository_interface(self):
        _check_ollama_available()

        from createagents.application.interfaces.chat_repository import (
            ChatRepository,
        )

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)

    @pytest.mark.asyncio
    async def test_chat_with_long_conversation_history(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

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
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 100,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestOllamaChatAdapterToolsIntegration:
    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_get_date(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
    async def test_chat_with_currentdate_tool_multiple_actions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response1 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask='What is the current Unix timestamp? Use the current_date tool.',
        )

        assert isinstance(response1, str)
        assert len(response1) > 0

        response2 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask='What is the current date and time in America/New_York? Use the current_date tool.',
        )

        assert response2 is not None
        assert isinstance(response2, str)
        assert len(response2) > 0

    @pytest.mark.asyncio
    async def test_chat_with_currentdate_tool_different_timezones(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        timezones = ['UTC', 'America/Sao_Paulo']

        for tz in timezones:
            response = await adapter.chat(
                model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        import os

        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        tool_names = [t.name for t in tools]
        if 'read_local_file' not in tool_names:
            pytest.skip(
                'ReadLocalFileTool not available (missing optional dependencies)'
            )

        file_path = os.path.abspath('.fixtures/sample_text.txt')

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        import os

        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        tool_names = [t.name for t in tools]
        if 'read_local_file' not in tool_names:
            pytest.skip(
                'ReadLocalFileTool not available (missing optional dependencies)'
            )

        file_path = os.path.abspath('.fixtures/sample_data.csv')

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'temperature': 0.7,
            'max_tokens': 200,
            'top_p': 0.9,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        response1 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC?",
        )

        assert response1 is not None
        assert isinstance(response1, str)
        history: list[dict[str, str]] = [
            {'role': 'user', 'content': "What is today's date in UTC?"},
            {'role': 'assistant', 'content': response1},
        ]

        response2 = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='You are a helpful assistant. Use tools when appropriate.',
            config={},
            tools=tools,
            history=history,
            user_ask='What time is it now in America/Sao_Paulo?',
        )

        assert response2 is not None
        assert isinstance(response2, str)
        assert len(response2) > 0

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_think_config(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'think': True,
            'temperature': 0.5,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions='Think step by step. Use tools when needed.',
            config=config,
            tools=tools,
            history=[],
            user_ask='What is the current Unix timestamp? Think about it first.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_top_k_config(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'top_k': 50,
            'max_tokens': 200,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Use tools to get accurate information.',
            config=config,
            tools=tools,
            history=[],
            user_ask="What is today's date in America/Sao_Paulo?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_all_configs_ollama(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from createagents.infra.adapters.tools.available_tools import (
            AvailableTools,
        )

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_all_tool_instances().values())

        config = {
            'temperature': 0.6,
            'max_tokens': 180,
            'top_p': 0.88,
            'top_k': 40,
            'think': False,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer using all available information and tools.',
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
class TestOllamaChatAdapterConfigValidation:
    @pytest.mark.asyncio
    async def test_chat_with_boundary_max_tokens_values(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config_min = {'max_tokens': 1}
        response_min = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config_min = {'top_p': 0.0}
        response_min = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer.',
            config=config_min,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response_min is not None

        config_max = {'top_p': 1.0}
        response_max = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer.',
            config=config_max,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response_max is not None

    @pytest.mark.asyncio
    async def test_chat_with_mixed_configs_at_boundaries(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.0,
            'max_tokens': 50,
            'top_p': 1.0,
            'top_k': 1,
            'think': True,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions='Answer.',
            config=config,
            tools=None,
            history=[],
            user_ask='Hi',
        )

        assert response is not None
        assert isinstance(response, str)


@pytest.mark.integration
class TestOllamaChatAdapterConfigEdgeCases:
    @pytest.mark.asyncio
    async def test_chat_with_all_configs_combined(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.5,
            'max_tokens': 100,
            'top_p': 0.8,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is Python?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_only_temperature_config(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {'temperature': 0.3}

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {'max_tokens': 200}

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
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
    async def test_chat_with_only_top_p_config(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {'top_p': 0.7}

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain ML.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_temperature_and_max_tokens(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.4,
            'max_tokens': 80,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Be concise.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is coding?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_temperature_and_top_p(self):
        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.6,
            'top_p': 0.85,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions='Be helpful.',
            config=config,
            tools=None,
            history=[],
            user_ask='Tell me about data.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_max_tokens_and_top_p(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            'max_tokens': 120,
            'top_p': 0.75,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer concisely.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain algorithms.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_boundary_temperature_values(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config_min = {'temperature': 0.0}
        response_min = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Be consistent.',
            config=config_min,
            tools=None,
            history=[],
            user_ask='Say hi.',
        )

        assert response_min is not None
        assert isinstance(response_min, str)

        config_max = {'temperature': 2.0}
        response_max = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Be creative.',
            config=config_max,
            tools=None,
            history=[],
            user_ask='Say hello.',
        )

        assert response_max is not None
        assert isinstance(response_max, str)

    @pytest.mark.asyncio
    async def test_chat_with_think_config_enabled(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {'think': True}

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions='Think step by step before answering.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is 15 * 8?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_think_config_disabled(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {'think': False}

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions='Answer directly without thinking.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is 15 * 8?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_top_k_config(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {'top_k': 40}

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain machine learning.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_top_k_boundary_values(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config_small = {'top_k': 1}
        response_small = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config=config_small,
            tools=None,
            history=[],
            user_ask='Hello',
        )

        assert response_small is not None
        assert isinstance(response_small, str)

        config_large = {'top_k': 100}
        response_large = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer briefly.',
            config=config_large,
            tools=None,
            history=[],
            user_ask='Hello',
        )

        assert response_large is not None
        assert isinstance(response_large, str)

    @pytest.mark.asyncio
    async def test_chat_with_temperature_top_k_think_combined(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.6,
            'top_k': 50,
            'think': True,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions='Think carefully and be thoughtful.',
            config=config,
            tools=None,
            history=[],
            user_ask='What is the difference between ML and AI?',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_all_supported_configs_ollama(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 150,
            'top_p': 0.85,
            'top_k': 45,
            'think': False,
        }

        response = await adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions='Answer helpfully.',
            config=config,
            tools=None,
            history=[],
            user_ask='Explain quantum computing.',
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        assert metrics[-1].success
