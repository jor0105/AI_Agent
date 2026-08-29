import json
import os
from typing import Any

import pytest

from createagents.application.interfaces import ChatRepository
from createagents.domain import (
    BaseTool,
    ChatMetrics,
    InvalidAgentConfigException,
    InvalidProviderException,
)
from createagents.infra import (
    AvailableTools,
    ChatAdapterFactory,
)
from createagents.main import CreateAgent

IA_OLLAMA_TEST_1: str = 'granite4:latest'
IA_OLLAMA_TEST_2: str = 'gpt-oss:120b-cloud'
IA_OPENAI_TEST_1: str = 'gpt-4.1-mini'
IA_OPENAI_TEST_2: str = 'gpt-5-nano'

# allow-assertion-reduction: Replaced broad exception swallowing with specific public-contract assertions during facade relocation.


def _get_openai_api_key() -> str:
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


def _check_ollama_model_available(model: str) -> None:
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


class _SimpleTool(BaseTool):
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def execute(self, *args: object, **kwargs: object) -> str:
        return 'simple-result'


class _StubChatRepository(ChatRepository):
    def __init__(self) -> None:
        self._metrics: list[ChatMetrics] = []
        self._call_count = 0

    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str:
        self._call_count += 1
        self._metrics.append(
            ChatMetrics(
                model=model,
                latency_ms=12.5,
                tokens_used=5,
                success=True,
            )
        )
        return f'Stub response #{self._call_count} to: {user_ask}'

    def get_metrics(self) -> list[ChatMetrics]:
        return self._metrics


@pytest.fixture
def stub_chat_repository(monkeypatch) -> _StubChatRepository:
    stub_repo = _StubChatRepository()

    def _fake_create(
        cls: type[ChatAdapterFactory], provider: str
    ) -> ChatRepository:
        return stub_repo

    monkeypatch.setattr(
        ChatAdapterFactory,
        'create',
        classmethod(_fake_create),
    )

    return stub_repo


@pytest.mark.integration
class TestCreateAgentInitializationErrors:
    def test_initialization_with_empty_model_raises_error(self):
        _get_openai_api_key()
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider='openai',
                model='',
                name='Test Agent',
                instructions='Be helpful',
            )

    def test_initialization_with_empty_name_raises_error(self):
        _get_openai_api_key()
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider='openai',
                model='gpt-5-mini',
                name='',
                instructions='Be helpful',
            )

    def test_initialization_with_empty_instructions_raises_error(self):
        _get_openai_api_key()
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider='openai',
                model='gpt-5-mini',
                name='Test Agent',
                instructions='',
            )

    def test_initialization_with_none_name(self):
        _get_openai_api_key()
        agent = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name=None,
            instructions='Be helpful',
        )
        configs = agent.get_configs()
        assert configs['name'] is None

    def test_initialization_with_none_instructions(self):
        _get_openai_api_key()
        agent = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test Agent',
            instructions=None,
        )
        configs = agent.get_configs()
        assert configs['instructions'] is None

    def test_initialization_with_both_none(self):
        _get_openai_api_key()
        agent = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name=None,
            instructions=None,
        )
        configs = agent.get_configs()
        assert configs['name'] is None
        assert configs['instructions'] is None

    def test_initialization_with_only_required_fields(self):
        _get_openai_api_key()
        agent = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
        )
        configs = agent.get_configs()
        assert configs['provider'] == 'openai'
        assert configs['model'] == 'gpt-5-mini'
        assert configs['name'] is None
        assert configs['instructions'] is None

    def test_initialization_with_invalid_provider_raises_error(self):
        with pytest.raises(InvalidProviderException):
            CreateAgent(
                provider='invalid_provider_xyz',
                model='gpt-5-mini',
                name='Test Agent',
                instructions='Be helpful',
            )

    def test_initialization_with_zero_history_max_size_raises_error(self):
        _get_openai_api_key()
        with pytest.raises(
            InvalidAgentConfigException, match='history_max_size'
        ):
            CreateAgent(
                provider='openai',
                model='gpt-5-mini',
                name='Test Agent',
                instructions='Be helpful',
                history_max_size=0,
            )

    def test_initialization_with_negative_history_max_size_raises_error(self):
        _get_openai_api_key()
        with pytest.raises(
            InvalidAgentConfigException, match='history_max_size'
        ):
            CreateAgent(
                provider='openai',
                model='gpt-5-mini',
                name='Test Agent',
                instructions='Be helpful',
                history_max_size=-5,
            )


@pytest.mark.integration
class TestCreateAgentInitializationSuccessOpenAI:
    def test_initialization_with_openai_gpt4_mini(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Test Agent OpenAI',
            instructions='You are a helpful assistant',
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs['provider'] == 'openai'
        assert configs['model'] == IA_OPENAI_TEST_1
        assert configs['name'] == 'Test Agent OpenAI'

    def test_initialization_with_openai_gpt4_nano(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_2,
            name='Test Agent Nano',
            instructions='You are a helpful assistant',
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs['provider'] == 'openai'
        assert configs['model'] == IA_OPENAI_TEST_2

    def test_initialization_with_custom_config_openai(self):
        _get_openai_api_key()

        custom_config = {'temperature': 0.7, 'max_tokens': 500, 'top_p': 0.9}

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Custom Config Agent',
            instructions='Be creative',
            config=custom_config,
        )

        configs = agent.get_configs()
        assert configs['config'] == custom_config

    def test_initialization_with_custom_history_size_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Large History Agent',
            instructions='Remember our conversation',
            history_max_size=50,
        )

        configs = agent.get_configs()
        assert configs['history_max_size'] == 50


@pytest.mark.integration
class TestCreateAgentInitializationSuccessOllama:
    def test_initialization_with_ollama_phi4(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='Test Agent Ollama',
            instructions='You are a helpful assistant',
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs['provider'] == 'ollama'
        assert configs['model'] == IA_OLLAMA_TEST_1
        assert configs['name'] == 'Test Agent Ollama'

    def test_initialization_with_custom_config_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        custom_config = {
            'temperature': 0.5,
        }

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='Custom Config Ollama',
            instructions='Be precise',
            config=custom_config,
        )

        configs = agent.get_configs()
        assert configs['config'] == custom_config

    def test_initialization_with_custom_history_size_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='Small History Agent',
            instructions='Keep context',
            history_max_size=5,
        )

        configs = agent.get_configs()
        assert configs['history_max_size'] == 5


@pytest.mark.integration
class TestCreateAgentChatOpenAI:
    @pytest.mark.asyncio
    async def test_simple_chat_with_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Chat Agent',
            instructions='You are a helpful assistant. Answer briefly.',
        )

        response = await agent.chat('What is 2+2?')

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert '4' in response

    @pytest.mark.asyncio
    async def test_multiple_chats_with_history_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='History Agent',
            instructions='You are a helpful assistant. Remember the context.',
        )

        response1 = await agent.chat('My name is Jordan')
        assert response1 is not None

        response2 = await agent.chat('What is my name?')
        assert response2 is not None
        assert isinstance(response2, str)
        assert 'Jordan' in response2 or 'jordan' in response2.lower()

    @pytest.mark.asyncio
    async def test_chat_with_empty_message_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Empty Test Agent',
            instructions='Answer any question',
        )

        with pytest.raises(ValueError, match='message'):
            await agent.chat('')

    @pytest.mark.asyncio
    async def test_chat_with_long_message_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Long Message Agent',
            instructions='Summarize the text briefly.',
        )

        long_message = 'This is a test. ' * 100
        response = await agent.chat(long_message)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_unicode_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Unicode Agent',
            instructions='You are a multilingual assistant.',
        )

        response = await agent.chat('Olá! Como você está? 你好 🌍')

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestCreateAgentChatOllama:
    @pytest.mark.asyncio
    async def test_simple_chat_with_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_2)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_2,
            name='Chat Ollama Agent',
            instructions='You are a helpful assistant. Answer briefly.',
        )

        response = await agent.chat('What is 2+2?')

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_multiple_chats_with_history_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='History Ollama Agent',
            instructions='You are a helpful assistant. Always remember and recall information from previous messages when asked.',
        )

        response1 = await agent.chat('My favorite color is blue')
        assert response1 is not None

        response2 = await agent.chat('What is my favorite color?')
        assert response2 is not None
        assert isinstance(response2, str)
        assert 'blue' in response2.lower() or 'color' in response2.lower()

    @pytest.mark.asyncio
    async def test_chat_with_unicode_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='Unicode Ollama Agent',
            instructions='You are a multilingual assistant.',
        )

        response = await agent.chat('Olá! 🌍')

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestCreateAgentHistory:
    @pytest.mark.asyncio
    async def test_clear_history_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Clear History Agent',
            instructions='Remember our conversation.',
        )

        await agent.chat('My name is Jordan')

        configs = agent.get_configs()
        assert len(configs['history']) > 0

        agent.clear_history()

        configs = agent.get_configs()
        assert len(configs['history']) == 0

    @pytest.mark.asyncio
    async def test_clear_history_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='Clear History Ollama',
            instructions='Remember context.',
        )

        await agent.chat('Hello')

        configs = agent.get_configs()
        assert len(configs['history']) > 0

        agent.clear_history()

        configs = agent.get_configs()
        assert len(configs['history']) == 0

    @pytest.mark.asyncio
    async def test_history_max_size_enforcement_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Small History Agent',
            instructions='Chat briefly.',
            history_max_size=2,
        )

        await agent.chat('First message')
        await agent.chat('Second message')
        await agent.chat('Third message')

        configs = agent.get_configs()
        assert len(configs['history']) <= 2


@pytest.mark.integration
class TestCreateAgentMetrics:
    @pytest.mark.asyncio
    async def test_get_metrics_after_chat_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Metrics Agent',
            instructions='Answer briefly.',
        )

        await agent.chat('Hello')

        metrics = agent.get_metrics()

        assert metrics is not None
        assert isinstance(metrics, list)
        assert len(metrics) > 0

        first_metric = metrics[0]
        assert isinstance(first_metric, ChatMetrics)
        assert first_metric.model == IA_OPENAI_TEST_1
        assert first_metric.latency_ms > 0

    @pytest.mark.asyncio
    async def test_get_metrics_after_multiple_chats_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Multi Metrics Agent',
            instructions='Answer briefly.',
        )

        await agent.chat('First')
        await agent.chat('Second')
        await agent.chat('Third')

        metrics = agent.get_metrics()

        assert len(metrics) >= 3

    @pytest.mark.asyncio
    async def test_export_metrics_json_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='JSON Metrics Agent',
            instructions='Answer briefly.',
        )

        await agent.chat('Test')

        json_str = agent.export_metrics_json()

        assert json_str is not None
        assert isinstance(json_str, str)
        assert 'summary' in json_str
        assert 'metrics' in json_str

    @pytest.mark.asyncio
    async def test_export_metrics_prometheus_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Prom Metrics Agent',
            instructions='Answer briefly.',
        )

        await agent.chat('Test')

        prom_str = agent.export_metrics_prometheus()

        assert prom_str is not None
        assert isinstance(prom_str, str)
        assert 'chat_requests_total' in prom_str

    @pytest.mark.asyncio
    async def test_get_metrics_after_chat_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_1,
            name='Metrics Ollama Agent',
            instructions='Answer briefly.',
        )

        await agent.chat('Hello')

        metrics = agent.get_metrics()

        assert metrics is not None
        assert isinstance(metrics, list)
        assert len(metrics) > 0


@pytest.mark.integration
class TestCreateAgentGetConfigs:
    def test_get_configs_returns_all_fields_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Config Test Agent',
            instructions='Test instructions',
            config={'temperature': 0.7},
            history_max_size=15,
        )

        configs = agent.get_configs()

        assert 'provider' in configs
        assert 'model' in configs
        assert 'name' in configs
        assert 'instructions' in configs
        assert 'config' in configs
        assert 'history' in configs
        assert 'history_max_size' in configs

        assert configs['provider'] == 'openai'
        assert configs['model'] == IA_OPENAI_TEST_1
        assert configs['name'] == 'Config Test Agent'
        assert configs['history_max_size'] == 15

    def test_get_configs_returns_all_fields_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_2)

        agent = CreateAgent(
            provider='ollama',
            model=IA_OLLAMA_TEST_2,
            name='Config Ollama Agent',
            instructions='Test ollama',
            config={'temperature': 0.5},
            history_max_size=20,
        )

        configs = agent.get_configs()

        assert configs['provider'] == 'ollama'
        assert configs['model'] == IA_OLLAMA_TEST_2
        assert configs['history_max_size'] == 20


@pytest.mark.integration
class TestCreateAgentEdgeCases:
    @pytest.mark.asyncio
    async def test_agent_with_very_long_instructions_openai(self):
        _get_openai_api_key()

        long_instructions = 'You are a helpful assistant. ' * 100

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Long Instructions Agent',
            instructions=long_instructions,
        )

        response = await agent.chat('Hello')

        assert response is not None
        assert isinstance(response, str)

    def test_agent_with_special_characters_in_name(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Agent-Test_123!@#',
            instructions='Be helpful',
        )

        configs = agent.get_configs()
        assert configs['name'] == 'Agent-Test_123!@#'

    @pytest.mark.asyncio
    async def test_chat_after_clear_history_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Clear and Chat Agent',
            instructions='Remember context',
        )

        response1 = await agent.chat('My name is Alice')
        assert response1 is not None

        agent.clear_history()

        response2 = await agent.chat('What is my name?')
        assert response2 is not None

    @pytest.mark.asyncio
    async def test_multiple_agents_same_model_independent(self):
        _get_openai_api_key()

        agent1 = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Agent 1',
            instructions='You are agent 1',
        )

        agent2 = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_1,
            name='Agent 2',
            instructions='You are agent 2',
        )

        await agent1.chat('Hello from agent 1')

        configs2 = agent2.get_configs()
        assert len(configs2['history']) == 0

    @pytest.mark.asyncio
    async def test_agent_with_minimal_config(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_2,
            name='Minimal Agent',
            instructions='Be helpful',
        )

        response = await agent.chat('Hi')
        assert response is not None

        configs = agent.get_configs()
        assert configs['history_max_size'] == 10
        assert configs['config'] == {}


@pytest.mark.integration
class TestCreateAgentToolAndMetricsOffline:
    def test_get_system_available_tools_matches_registry(
        self, stub_chat_repository
    ):
        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_2,
            name='System Tools Agent',
            instructions='Inspect tools.',
        )

        expected_tools = AvailableTools.get_system_tools()
        assert agent.get_system_available_tools() == expected_tools

    def test_get_all_available_tools_merges_agent_tools(
        self, stub_chat_repository
    ):
        custom_tool = _SimpleTool('CustomTool', 'Runs diagnostics')

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_2,
            name='Custom Tool Agent',
            instructions='Use tools when needed.',
            tools=[custom_tool],
        )

        all_tools = agent.get_all_available_tools()
        system_tools = AvailableTools.get_system_tools()

        assert 'customtool' in all_tools
        assert all_tools['customtool'] == 'Runs diagnostics'
        assert set(system_tools.keys()).issubset(all_tools.keys())

    def test_get_all_available_tools_skips_system_duplicates(
        self, stub_chat_repository
    ):
        duplicate_tool = _SimpleTool('CurrentDate', 'duplicate description')

        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_2,
            name='Duplicate Tool Agent',
            instructions='Test duplicates.',
            tools=[duplicate_tool],
        )

        all_tools = agent.get_all_available_tools()
        system_tools = AvailableTools.get_system_tools()

        assert 'currentdate' in all_tools
        assert all_tools['currentdate'] == system_tools['currentdate']
        assert all_tools['currentdate'] != 'duplicate description'

    @pytest.mark.asyncio
    async def test_metrics_export_and_history_flow(
        self, stub_chat_repository, tmp_path
    ):
        agent = CreateAgent(
            provider='openai',
            model=IA_OPENAI_TEST_2,
            name='Metrics Export Agent',
            instructions='Track metrics.',
        )

        response = await agent.chat('Hello stub integration')
        assert isinstance(response, str)
        assert 'Stub response' in response

        metrics = agent.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OPENAI_TEST_2

        json_path = tmp_path / 'metrics.json'
        json_str = agent.export_metrics_json(str(json_path))
        data = json.loads(json_str)

        assert data['summary']['total_requests'] == 1
        assert data['metrics'][0]['model'] == IA_OPENAI_TEST_2
        assert json_path.read_text() == json_str

        prom_path = tmp_path / 'metrics.prom'
        prom_str = agent.export_metrics_prometheus(str(prom_path))
        assert 'chat_requests_total 1' in prom_str
        assert prom_path.read_text() == prom_str

        assert len(agent.get_configs()['history']) == 2
        agent.clear_history()
        assert len(agent.get_configs()['history']) == 0
