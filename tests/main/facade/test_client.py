from collections.abc import Sequence
from typing import cast
from unittest.mock import Mock, patch

import pytest

from createagents.domain import (
    BaseTool,
    ChatMetrics,
    InvalidAgentConfigException,
    InvalidBaseToolException,
    InvalidProviderException,
)
from createagents.main import CreateAgent


@pytest.mark.unit
class TestCreateAgentInitialization:
    def test_initialization_creates_agent(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test Agent',
            instructions='Be helpful',
        )

        configs = controller.get_configs()
        assert configs['provider'] == 'openai'
        assert configs['model'] == 'gpt-5'
        assert configs['name'] == 'Test Agent'
        assert configs['instructions'] == 'Be helpful'

    def test_initialization_with_ollama_provider(self):
        controller = CreateAgent(
            provider='ollama',
            model='gemma3:4b',
            name='Test',
            instructions='Test',
        )

        configs = controller.get_configs()
        assert configs['provider'] == 'ollama'
        assert configs['model'] == 'gemma3:4b'

    def test_initialization_creates_chat_use_case(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test',
            instructions='Test',
        )

        assert callable(controller.chat)

    def test_initialization_creates_get_config_use_case(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        configs = controller.get_configs()
        assert isinstance(configs, dict)
        assert configs['model'] == 'gpt-5-nano'

    def test_initialization_with_invalid_data_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider='openai', model='', name='Test', instructions='Test'
            )

    def test_initialization_with_custom_config(self):
        config = {'temperature': 0.7, 'max_tokens': 1000}
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            config=config,
        )

        configs = controller.get_configs()
        assert configs['config'] == config

    def test_initialization_with_custom_history_max_size(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            history_max_size=20,
        )

        configs = controller.get_configs()
        assert configs['history_max_size'] == 20

    def test_initialization_with_default_history_max_size(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
        )

        configs = controller.get_configs()
        assert configs['history_max_size'] == 10

    def test_initialization_with_invalid_provider_raises_error(self):
        with pytest.raises(InvalidProviderException):
            CreateAgent(
                provider='invalid_provider',
                model='gpt-5',
                name='Test',
                instructions='Test',
            )

    def test_initialization_with_none_name(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name=None,
            instructions='Test',
        )

        configs = controller.get_configs()
        assert configs['name'] is None

    def test_initialization_with_none_instructions(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions=None,
        )

        configs = controller.get_configs()
        assert configs['instructions'] is None

    def test_initialization_with_both_none(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name=None,
            instructions=None,
        )

        configs = controller.get_configs()
        assert configs['name'] is None
        assert configs['instructions'] is None

    def test_initialization_with_only_required_fields(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
        )

        configs = controller.get_configs()
        assert configs['provider'] == 'openai'
        assert configs['model'] == 'gpt-5'
        assert configs['name'] is None
        assert configs['instructions'] is None


@pytest.mark.unit
class TestCreateAgentChat:
    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_returns_response(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'AI response'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        response = await controller.chat('Hello')

        assert response == 'AI response'

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_calls_use_case_with_correct_params(
        self, mock_create_chat
    ):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test',
            instructions='Test',
        )

        await controller.chat('Test message')

        assert mock_use_case.execute.called
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == 'Test message'

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_with_empty_message(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        response = await controller.chat('')

        assert response == 'Response'
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == ''

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_when_use_case_raises_exception(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception('API Error'))
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        with pytest.raises(Exception, match='API Error'):
            await controller.chat('Hello')

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_multiple_chat_calls(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        await controller.chat('Message 1')
        await controller.chat('Message 2')

        assert mock_use_case.execute.call_count == 2

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_updates_agent_history(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'AI Response'

        async def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute = AsyncMock(side_effect=execute_side_effect)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        await controller.chat('Hello')

        configs = controller.get_configs()
        assert len(configs['history']) == 2


@pytest.mark.unit
class TestCreateAgentGetConfigs:
    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_config_use_case'
    )
    def test_get_configs_returns_dict(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.to_dict.return_value = {
            'name': 'Test',
            'model': 'gpt-5-nano',
            'instructions': 'Test',
            'history': [],
            'provider': 'openai',
        }
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        config = controller.get_configs()

        assert isinstance(config, dict)
        assert 'name' in config
        assert 'model' in config

    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_config_use_case'
    )
    def test_get_configs_calls_use_case(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.to_dict.return_value = {}
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        controller.get_configs()

        assert mock_use_case.execute.called

    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_config_use_case'
    )
    def test_get_configs_returns_all_expected_fields(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        expected_config = {
            'name': 'Test Agent',
            'model': 'gpt-5',
            'instructions': 'Be helpful',
            'history': [],
            'provider': 'openai',
            'config': {'temperature': 0.7},
            'history_max_size': 10,
        }
        mock_output.to_dict.return_value = expected_config
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test Agent',
            instructions='Be helpful',
        )

        config = controller.get_configs()

        assert config == expected_config

    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_config_use_case'
    )
    def test_get_configs_when_use_case_raises_exception(
        self, mock_create_config
    ):
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = Exception('Config Error')
        mock_create_config.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        with pytest.raises(Exception, match='Config Error'):
            controller.get_configs()


@pytest.mark.unit
class TestCreateAgentClearHistory:
    def test_clear_history_method_exists(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test',
            instructions='Test',
        )
        assert callable(controller.clear_history)

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_clear_history_clears_populated_history(
        self, mock_create_chat
    ):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'AI Response'

        async def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute = AsyncMock(side_effect=execute_side_effect)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test',
            instructions='Test',
        )

        await controller.chat('Message 1')
        await controller.chat('Message 2')
        assert len(controller.get_configs()['history']) == 4

        controller.clear_history()
        assert controller.get_configs()['history'] == []

        await controller.chat('New message')
        assert len(controller.get_configs()['history']) == 2

    def test_clear_history_preserves_agent_config(self):
        controller = CreateAgent(
            provider='ollama',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='Be helpful',
        )
        before = controller.get_configs()
        controller.clear_history()
        after = controller.get_configs()
        assert after['model'] == before['model']
        assert after['name'] == before['name']
        assert after['instructions'] == before['instructions']
        assert after['provider'] == before['provider']

    def test_clear_history_on_empty_history_is_idempotent(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test',
            instructions='Test',
        )
        assert controller.get_configs()['history'] == []
        controller.clear_history()
        assert controller.get_configs()['history'] == []
        controller.clear_history()
        assert controller.get_configs()['history'] == []


@pytest.mark.unit
class TestCreateAgentMetrics:
    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_get_metrics_returns_list(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5-nano', latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        metrics = controller.get_metrics()

        assert isinstance(metrics, list)
        assert len(metrics) == 1
        assert isinstance(metrics[0], ChatMetrics)

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_get_metrics_calls_use_case_method(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        controller.get_metrics()

        mock_use_case.get_metrics.assert_called_once()

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_get_metrics_when_adapter_has_no_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        metrics = controller.get_metrics()

        assert metrics == []

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_get_metrics_with_multiple_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5-nano', latency_ms=100.0, tokens_used=50),
            ChatMetrics(model='gpt-5-nano', latency_ms=150.0, tokens_used=75),
            ChatMetrics(model='gpt-5-nano', latency_ms=120.0, tokens_used=60),
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        metrics = controller.get_metrics()

        assert len(metrics) == 3
        assert all(isinstance(m, ChatMetrics) for m in metrics)

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_json(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5-nano', latency_ms=100.0, tokens_used=50)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert 'gpt-5-nano' in json_str
        assert 'summary' in json_str

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_json_to_file(self, mock_create_chat, tmp_path):
        import json

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5-nano', latency_ms=100.0, tokens_used=50)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        filepath = tmp_path / 'metrics.json'
        controller.export_metrics_json(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)

        assert 'summary' in data
        assert 'metrics' in data

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_prometheus(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5-nano', latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)
        assert 'chat_requests_total' in prom_text

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_prometheus_to_file(
        self, mock_create_chat, tmp_path
    ):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5-nano', latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        filepath = tmp_path / 'metrics.prom'
        controller.export_metrics_prometheus(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            content = f.read()

        assert 'chat_requests_total' in content

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_json_with_empty_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert 'summary' in json_str

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_prometheus_with_empty_metrics(
        self, mock_create_chat
    ):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)


@pytest.mark.unit
class TestCreateAgentIntegration:
    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_and_get_configs_together(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        response = await controller.chat('Hello')
        assert response == 'Response'

        configs = controller.get_configs()
        assert isinstance(configs, dict)

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_clear_history_chat_again(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'

        async def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute = AsyncMock(side_effect=execute_side_effect)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        await controller.chat('Message 1')
        assert len(controller.get_configs()['history']) == 2

        controller.clear_history()
        assert len(controller.get_configs()['history']) == 0

        await controller.chat('Message 2')
        assert len(controller.get_configs()['history']) == 2


@pytest.mark.unit
class TestCreateAgentEdgeCases:
    def test_initialization_with_very_long_instructions(self):
        long_instructions = 'A' * 10000
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions=long_instructions,
        )

        configs = controller.get_configs()
        assert configs['instructions'] == long_instructions

    def test_initialization_with_special_characters_in_name(self):
        special_name = 'Test-Agent_123!@#$%'
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name=special_name,
            instructions='Test',
        )

        configs = controller.get_configs()
        assert configs['name'] == special_name

    def test_initialization_with_unicode_characters(self):
        unicode_name = '测试代理 🤖'
        unicode_instructions = 'Seja útil e educado 你好'

        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name=unicode_name,
            instructions=unicode_instructions,
        )

        configs = controller.get_configs()
        assert configs['name'] == unicode_name
        assert configs['instructions'] == unicode_instructions

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_with_very_long_message(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        long_message = 'A' * 50000
        response = await controller.chat(long_message)

        assert response == 'Response'
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == long_message

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_with_unicode_message(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = '回复'
        mock_use_case.execute = AsyncMock(return_value=mock_output)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        unicode_message = '你好\uff0c世界\uff01 🌍'
        response = await controller.chat(unicode_message)

        assert response == '回复'

    def test_initialization_with_history_max_size_zero(self):
        with pytest.raises(
            InvalidAgentConfigException, match='history_max_size'
        ):
            CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                history_max_size=0,
            )

    def test_initialization_with_negative_history_max_size(self):
        with pytest.raises(
            InvalidAgentConfigException, match='history_max_size'
        ):
            CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                history_max_size=-1,
            )

    def test_initialization_with_empty_config_dict(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            config={},
        )

        configs = controller.get_configs()
        assert configs['config'] == {}

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_to_nonexistent_directory(
        self, mock_create_chat, tmp_path
    ):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5', latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        nonexistent_path = tmp_path / 'nonexistent' / 'metrics.json'

        with pytest.raises(FileNotFoundError):
            controller.export_metrics_json(str(nonexistent_path))

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_preserves_message_order(self, mock_create_chat):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'

        async def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute = AsyncMock(side_effect=execute_side_effect)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        await controller.chat('First message')
        await controller.chat('Second message')
        await controller.chat('Third message')

        history = controller.get_configs()['history']

        assert len(history) == 6
        assert history[0]['content'] == 'First message'
        assert history[2]['content'] == 'Second message'
        assert history[4]['content'] == 'Third message'

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_get_metrics_does_not_modify_internal_state(
        self, mock_create_chat
    ):
        mock_use_case = Mock()

        def get_metrics_side_effect():
            return [ChatMetrics(model='gpt-5', latency_ms=100.0)]

        mock_use_case.get_metrics.side_effect = get_metrics_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        metrics1 = controller.get_metrics()
        metrics1.clear()
        metrics2 = controller.get_metrics()
        assert len(metrics2) == 1

    def test_controller_has_all_required_methods(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5-mini',
            name='Test Agent',
            instructions='Test instructions',
        )

        assert callable(controller.chat)
        assert callable(controller.get_configs)
        assert callable(controller.clear_history)
        assert callable(controller.get_metrics)
        assert callable(controller.export_metrics_json)
        assert callable(controller.export_metrics_prometheus)

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_json_without_filepath(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5', latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert len(json_str) > 0
        assert 'summary' in json_str

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    def test_export_metrics_prometheus_without_filepath(
        self, mock_create_chat
    ):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model='gpt-5', latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)
        assert len(prom_text) > 0

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_clear_history_with_chat_and_get_configs(
        self, mock_create_chat
    ):
        from unittest.mock import AsyncMock

        mock_chat_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'

        async def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_chat_use_case.execute = AsyncMock(side_effect=execute_side_effect)
        mock_create_chat.return_value = mock_chat_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        await controller.chat('Hello')
        configs = controller.get_configs()
        assert len(configs['history']) == 2

        controller.clear_history()
        assert len(controller.get_configs()['history']) == 0

        await controller.chat('New conversation')
        assert len(controller.get_configs()['history']) == 2

    def test_initialization_with_all_optional_params_none(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name=None,
            instructions=None,
            config=None,
        )

        configs = controller.get_configs()
        assert configs['name'] is None
        assert configs['instructions'] is None
        assert configs['config'] == {}

    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_multiple_consecutive_clear_history_calls(
        self, mock_create_chat
    ):
        from unittest.mock import AsyncMock

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = 'Response'

        async def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute = AsyncMock(side_effect=execute_side_effect)
        mock_create_chat.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        await controller.chat('Message')
        assert len(controller.get_configs()['history']) == 2

        controller.clear_history()
        controller.clear_history()
        controller.clear_history()

        assert len(controller.get_configs()['history']) == 0

        controller.clear_history()
        assert len(controller.get_configs()['history']) == 0

    def test_initialization_provider_case_variations(self):
        providers = ['openai', 'OPENAI', 'OpenAI', 'oPeNaI']

        for provider in providers:
            controller = CreateAgent(
                provider=provider,
                model='gpt-5',
                name='Test',
                instructions='Test',
            )

            configs = controller.get_configs()
            assert configs['provider'].lower() == 'openai'

    def test_initialization_with_tools_none(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=None,
        )

        configs = controller.get_configs()
        assert configs['tools'] is None

    def test_initialization_with_tools_empty_list(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[],
        )

        configs = controller.get_configs()
        assert configs['tools'] is None

    def test_initialization_with_single_tool(self):
        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        configs = controller.get_configs()
        assert len(configs['tools']) == 1

    def test_initialization_with_multiple_tools(self):
        from createagents.domain import BaseTool

        class Tool1(BaseTool):
            name = 'tool1'
            description = 'First tool'

            def execute(self, **kwargs):
                return 'result1'

        class Tool2(BaseTool):
            name = 'tool2'
            description = 'Second tool'

            def execute(self, **kwargs):
                return 'result2'

        tools = [Tool1(), Tool2()]
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=tools,
        )

        configs = controller.get_configs()
        assert len(configs['tools']) == 2

    def test_initialization_with_string_tool_name(self):
        from createagents.infra import AvailableTools

        available = AvailableTools.get_system_tools()
        if available:
            tool_name = next(iter(available))
            controller = CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                tools=[tool_name],
            )

            configs = controller.get_configs()
            assert configs['tools'] is not None
        else:
            pytest.skip('No available tools to test')

    def test_initialization_with_mixed_tool_types(self):
        from createagents.domain import BaseTool
        from createagents.infra import AvailableTools

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        available = AvailableTools.get_system_tools()
        if available:
            tool_name = next(iter(available))
            controller = CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                tools=[tool, tool_name],
            )

            configs = controller.get_configs()
            assert len(configs['tools']) == 2
        else:
            controller = CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                tools=[tool],
            )
            configs = controller.get_configs()
            assert len(configs['tools']) == 1

    def test_get_configs_includes_tools(self):
        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        config = controller.get_configs()

        assert 'tools' in config

    @pytest.mark.asyncio
    async def test_initialization_tools_preserved_through_chat(self):
        from unittest.mock import AsyncMock, Mock, patch

        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()

        with patch(
            'createagents.main.facade.client.AgentComposer.create_chat_use_case'
        ) as mock_create_chat:
            mock_use_case = Mock()
            mock_output = Mock()
            mock_output.response = 'Response'
            mock_use_case.execute = AsyncMock(return_value=mock_output)
            mock_create_chat.return_value = mock_use_case

            controller = CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                tools=[tool],
            )

            await controller.chat(' Hello')

            configs = controller.get_configs()
            assert len(configs['tools']) == 1

    def test_initialization_with_invalid_tool_type_raises_error(self):
        with pytest.raises(InvalidBaseToolException):
            CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                tools=cast(Sequence[str | BaseTool], [123]),
            )

    def test_initialization_with_tool_missing_attributes_raises_error(self):
        class InvalidTool:
            __slots__ = ()

        with pytest.raises(InvalidBaseToolException):
            CreateAgent(
                provider='openai',
                model='gpt-5',
                name='Test',
                instructions='Test',
                tools=cast(Sequence[str | BaseTool], [InvalidTool()]),
            )


@pytest.mark.unit
class TestCreateAgentGetSystemAvailableTools:
    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_system_available_tools_use_case'
    )
    def test_get_system_available_tools_returns_dict(
        self, mock_create_use_case
    ):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            'currentdate': 'Get current date'
        }
        mock_create_use_case.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        tools = controller.get_system_available_tools()

        assert isinstance(tools, dict)
        assert 'currentdate' in tools

    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_system_available_tools_use_case'
    )
    def test_get_system_available_tools_calls_use_case(
        self, mock_create_use_case
    ):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {}
        mock_create_use_case.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        controller.get_system_available_tools()

        mock_use_case.execute.assert_called_once()

    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_system_available_tools_use_case'
    )
    def test_get_system_available_tools_with_multiple_tools(
        self, mock_create_use_case
    ):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            'currentdate': 'Get current date',
            'readlocalfile': 'Read local file content',
        }
        mock_create_use_case.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        tools = controller.get_system_available_tools()

        assert len(tools) == 2
        assert 'currentdate' in tools
        assert 'readlocalfile' in tools

    @patch(
        'createagents.main.facade.client.AgentComposer.create_get_system_available_tools_use_case'
    )
    def test_get_system_available_tools_empty(self, mock_create_use_case):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {}
        mock_create_use_case.return_value = mock_use_case

        controller = CreateAgent(
            provider='openai', model='gpt-5', name='Test', instructions='Test'
        )

        tools = controller.get_system_available_tools()

        assert tools == {}


@pytest.mark.unit
class TestCreateAgentGetAllAvailableTools:
    def test_get_all_available_tools_includes_system_tools(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
        )

        tools = controller.get_all_available_tools()

        assert isinstance(tools, dict)
        assert 'currentdate' in tools

    def test_get_all_available_tools_includes_agent_tools(self):
        from createagents.domain import BaseTool

        class CustomTool(BaseTool):
            name = 'custom_tool'
            description = 'A custom tool for testing'

            def execute(self, **kwargs):
                return 'custom result'

        tool = CustomTool()
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        tools = controller.get_all_available_tools()

        assert isinstance(tools, dict)
        assert 'currentdate' in tools
        assert 'custom_tool' in tools
        assert tools['custom_tool'] == 'A custom tool for testing'

    def test_get_all_available_tools_with_multiple_agent_tools(self):
        from createagents.domain import BaseTool

        class Tool1(BaseTool):
            name = 'tool1'
            description = 'First custom tool'

            def execute(self, **kwargs):
                return 'result1'

        class Tool2(BaseTool):
            name = 'tool2'
            description = 'Second custom tool'

            def execute(self, **kwargs):
                return 'result2'

        tools_list = [Tool1(), Tool2()]
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=tools_list,
        )

        tools = controller.get_all_available_tools()

        assert isinstance(tools, dict)
        assert 'currentdate' in tools
        assert 'tool1' in tools
        assert 'tool2' in tools
        assert tools['tool1'] == 'First custom tool'
        assert tools['tool2'] == 'Second custom tool'

    def test_get_all_available_tools_without_agent_tools(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=None,
        )

        tools = controller.get_all_available_tools()

        assert isinstance(tools, dict)
        assert 'currentdate' in tools

    def test_get_all_available_tools_with_empty_tools_list(self):
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[],
        )

        tools = controller.get_all_available_tools()

        assert isinstance(tools, dict)
        assert 'currentdate' in tools

    def test_get_all_available_tools_case_insensitive(self):
        from createagents.domain import BaseTool

        class CustomTool(BaseTool):
            name = 'CustomTool'
            description = 'A tool with mixed case name'

            def execute(self, **kwargs):
                return 'result'

        tool = CustomTool()
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        tools = controller.get_all_available_tools()

        assert 'customtool' in tools

    def test_get_all_available_tools_does_not_modify_agent(self):
        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'Test'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        controller = CreateAgent(
            provider='openai',
            model='gpt-5',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        tools = controller.get_all_available_tools()
        tools['fake_tool'] = 'fake description'

        tools_again = controller.get_all_available_tools()
        assert 'fake_tool' not in tools_again
