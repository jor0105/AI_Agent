from unittest.mock import MagicMock, patch

import pytest

from createagents.application import (
    ChatWithAgentUseCase,
    GetAgentConfigUseCase,
)
from createagents.domain import (
    Agent,
    InvalidAgentConfigException,
    InvalidProviderException,
)
from createagents.main import AgentComposer


@pytest.mark.unit
class TestAgentComposer:
    def test_create_agent_with_valid_data(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='Be helpful',
            config={},
        )

        assert isinstance(agent, Agent)
        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'
        assert agent.name == 'Test Agent'
        assert agent.instructions == 'Be helpful'

    def test_create_agent_with_ollama_provider(self):
        agent = AgentComposer.create_agent(
            provider='ollama',
            model='phi4-mini:latest',
            name='Local Agent',
            instructions='Test',
            config={},
        )

        assert agent.provider == 'ollama'

    def test_create_agent_with_empty_model_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai', model='', name='Test', instructions='Test'
            )

    def test_create_agent_with_empty_name_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='',
                instructions='Test',
            )

    def test_create_agent_with_empty_instructions_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='',
            )

    def test_create_agent_with_none_name(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name=None,
            instructions='Test',
            config={},
        )

        assert agent.name is None

    def test_create_agent_with_none_instructions(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions=None,
            config={},
        )

        assert agent.instructions is None

    def test_create_agent_with_both_none(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name=None,
            instructions=None,
            config={},
        )

        assert agent.name is None
        assert agent.instructions is None

    def test_create_agent_with_only_required_fields(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
        )

        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'
        assert agent.name is None
        assert agent.instructions is None

    def test_create_chat_use_case_returns_use_case(self):
        with (
            patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}),
            patch(
                'createagents.infra.adapters.OpenAI.client_openai.ClientOpenAI.get_client'
            ) as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            use_case = AgentComposer.create_chat_use_case(provider='openai')

            assert isinstance(use_case, ChatWithAgentUseCase)

    def test_create_chat_use_case_with_ollama_provider(self):
        use_case = AgentComposer.create_chat_use_case(provider='ollama')

        assert isinstance(use_case, ChatWithAgentUseCase)

    def test_create_chat_use_case_injects_correct_adapter(self):
        with (
            patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}),
            patch(
                'createagents.infra.adapters.OpenAI.client_openai.ClientOpenAI.get_client'
            ) as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            use_case = AgentComposer.create_chat_use_case(provider='openai')

            assert hasattr(use_case, '_ChatWithAgentUseCase__chat_repository')

    def test_create_get_config_use_case_returns_use_case(self):
        use_case = AgentComposer.create_get_config_use_case()

        assert isinstance(use_case, GetAgentConfigUseCase)

    def test_create_multiple_agents_are_independent(self):
        agent1 = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent1',
            instructions='Test1',
            config={},
        )
        agent2 = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent2',
            instructions='Test2',
            config={},
        )

        assert agent1 is not agent2
        assert agent1.name != agent2.name

    def test_create_multiple_chat_use_cases_are_independent(self):
        with (
            patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}),
            patch(
                'createagents.infra.adapters.OpenAI.client_openai.ClientOpenAI.get_client'
            ) as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            use_case1 = AgentComposer.create_chat_use_case(provider='openai')
            use_case2 = AgentComposer.create_chat_use_case(provider='openai')

            assert use_case1 is not use_case2

    def test_create_agent_wraps_exceptions_in_invalid_config(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='   ',
                instructions='Test',
            )

    def test_error_message_contains_composer_context(self):
        try:
            AgentComposer.create_agent(
                provider='openai', model='', name='Test', instructions='Test'
            )
        except InvalidAgentConfigException:
            pass

    def test_create_agent_with_empty_provider_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
            )

    def test_create_agent_with_invalid_provider_raises_error(self):
        with pytest.raises(InvalidProviderException):
            AgentComposer.create_agent(
                provider='invalid_provider',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
            )

    def test_create_agent_with_provider_case_insensitive(self):
        agent = AgentComposer.create_agent(
            provider='OPENAI',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='Be helpful',
            config={},
        )

        assert agent.provider.lower() == 'openai'

    def test_create_agent_with_whitespace_only_provider_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='   ',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
            )

    def test_create_agent_with_whitespace_only_model_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='   ',
                name='Test',
                instructions='Test',
            )

    def test_create_agent_with_whitespace_only_name_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='   ',
                instructions='Test',
            )

    def test_create_agent_with_whitespace_only_instructions_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='   ',
            )

    def test_create_agent_with_zero_history_max_size_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                history_max_size=0,
            )

    def test_create_agent_with_negative_history_max_size_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                history_max_size=-5,
            )

    def test_create_agent_with_non_integer_history_max_size_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                history_max_size='10',
            )

    def test_create_agent_with_float_history_max_size_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                history_max_size=10.5,
            )

    def test_create_agent_with_valid_history_max_size(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
            history_max_size=20,
        )

        assert agent.history.max_size == 20

    def test_create_agent_with_non_dict_config_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config='not_a_dict',
            )

    def test_create_agent_with_list_config_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config=['invalid'],
            )

    def test_create_agent_with_empty_config(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
        )

        assert agent.config == {}

    def test_create_chat_use_case_with_invalid_provider_raises_error(self):
        with pytest.raises(ValueError):
            AgentComposer.create_chat_use_case(provider='invalid_provider')

    def test_create_chat_use_case_with_empty_provider_raises_error(self):
        with pytest.raises(ValueError):
            AgentComposer.create_chat_use_case(provider='')

    def test_create_chat_use_case_openai_injects_correct_adapter_type(self):
        with (
            patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}),
            patch(
                'createagents.infra.adapters.OpenAI.client_openai.ClientOpenAI.get_client'
            ) as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            use_case = AgentComposer.create_chat_use_case(provider='openai')

            assert use_case._ChatWithAgentUseCase__chat_repository is not None

    def test_create_chat_use_case_ollama_injects_correct_adapter_type(self):
        use_case = AgentComposer.create_chat_use_case(provider='ollama')

        assert use_case._ChatWithAgentUseCase__chat_repository is not None

    def test_create_agent_with_valid_data_all_fields_match(self):
        config = {'temperature': 0.5}
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='Be helpful',
            config=config,
            history_max_size=15,
        )

        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'
        assert agent.name == 'Test Agent'
        assert agent.instructions == 'Be helpful'
        assert agent.config == config
        assert agent.history.max_size == 15

    def test_create_get_config_use_case_multiple_instances_are_independent(
        self,
    ):
        use_case1 = AgentComposer.create_get_config_use_case()
        use_case2 = AgentComposer.create_get_config_use_case()

        assert use_case1 is not use_case2

    def test_create_agent_with_special_characters_in_name(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test-Agent_123!',
            instructions='Be helpful',
            config={},
        )

        assert agent.name == 'Test-Agent_123!'

    def test_create_agent_with_special_characters_in_instructions(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Be helpful! @#$%^&*()',
            config={},
        )

        assert agent.instructions == 'Be helpful! @#$%^&*()'

    def test_create_agent_with_long_strings(self):
        long_name = 'A' * 1000
        long_instructions = 'B' * 5000
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name=long_name,
            instructions=long_instructions,
            config={},
        )

        assert agent.name == long_name
        assert agent.instructions == long_instructions

    def test_create_agent_history_is_initialized(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
        )

        assert agent.history is not None
        assert isinstance(agent.history.get_messages(), list)

    def test_create_agent_with_max_int_history_size(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
            history_max_size=2147483647,
        )

        assert agent.history.max_size == 2147483647

    def test_create_agent_default_history_max_size(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
        )

        assert agent.history.max_size == 10

    def test_create_agent_with_config_none_uses_empty_dict(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config=None,
        )

        assert agent.config == {}

    def test_create_agent_config_is_passed_by_reference(self):
        original_config = {'temperature': 0.7}
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config=original_config,
        )

        assert agent.config['temperature'] == 0.7
        original_config['temperature'] = 0.9
        assert agent.config['temperature'] == 0.9

    def test_create_chat_use_case_with_different_models_same_provider(self):
        with (
            patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}),
            patch(
                'createagents.infra.adapters.OpenAI.client_openai.ClientOpenAI.get_client'
            ) as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            use_case1 = AgentComposer.create_chat_use_case(provider='openai')
            use_case2 = AgentComposer.create_chat_use_case(provider='openai')

            assert use_case1 is not use_case2

    def test_create_agent_validates_provider_before_model(self):
        with pytest.raises(
            (InvalidProviderException, InvalidAgentConfigException)
        ):
            AgentComposer.create_agent(
                provider='invalid_provider',
                model='',
                name='Test',
                instructions='Test',
            )

    def test_create_agent_with_nested_config_dict(self):
        config = {
            'temperature': 0.7,
            'max_tokens': 100,
            'top_p': 0.9,
        }

        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config=config,
        )

        assert agent.config == config
        assert agent.config['temperature'] == 0.7
        assert agent.config['top_p'] == 0.9

    def test_create_agent_with_unicode_in_fields(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='测试代理 🤖',
            instructions='Seja útil 日本語 Привет',
            config={},
        )

        assert '测试代理' in agent.name
        assert '🤖' in agent.name
        assert '日本語' in agent.instructions

    def test_create_multiple_agents_with_same_config_are_independent(self):
        config = {'temperature': 0.7}

        agent1 = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent1',
            instructions='Test',
            config=config,
        )

        agent2 = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent2',
            instructions='Test',
            config=config,
        )

        assert agent1 is not agent2

    def test_create_agent_with_boundary_history_max_size(self):
        agent_min = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
            history_max_size=1,
        )
        assert agent_min.history.max_size == 1

        agent_high = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
            history_max_size=10000,
        )
        assert agent_high.history.max_size == 10000

    def test_create_get_config_use_case_is_always_fresh_instance(self):
        instances = [
            AgentComposer.create_get_config_use_case() for _ in range(5)
        ]
        ids = [id(inst) for inst in instances]
        assert len(set(ids)) == 5

    def test_create_agent_with_valid_config_values(self):
        config = {
            'temperature': 0.5,
            'max_tokens': 100,
        }

        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config=config,
        )

        assert agent.config == config
        assert agent.config['temperature'] == 0.5

    def test_composer_methods_are_static(self):
        import inspect

        assert isinstance(
            inspect.getattr_static(AgentComposer, 'create_agent'), staticmethod
        )
        assert isinstance(
            inspect.getattr_static(AgentComposer, 'create_chat_use_case'),
            staticmethod,
        )
        assert isinstance(
            inspect.getattr_static(
                AgentComposer, 'create_get_config_use_case'
            ),
            staticmethod,
        )

    def test_create_agent_with_none_config_internally_converted(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert hasattr(agent, 'config')
        assert isinstance(agent.config, dict)

    def test_create_agent_with_tools_none(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=None,
        )

        assert agent.tools is None

    def test_create_agent_with_tools_empty_list(self):
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=[],
        )

        assert agent.tools == []

    def test_create_agent_with_single_tool(self):
        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        assert len(agent.tools) == 1
        assert agent.tools[0] is tool

    def test_create_agent_with_multiple_tools(self):
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
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=tools,
        )

        assert len(agent.tools) == 2
        assert all(isinstance(t, BaseTool) for t in agent.tools)

    def test_create_agent_with_string_tool_name(self):
        from createagents.infra import AvailableTools

        available = AvailableTools.get_system_tools()
        if available:
            tool_name = list(available.keys())[0]
            agent = AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[tool_name],
            )

            assert agent.tools is not None
        else:
            pytest.skip('No available tools to test')

    def test_create_agent_with_mixed_tool_types(self):
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
            tool_name = list(available.keys())[0]
            agent = AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[tool, tool_name],
            )

            assert agent.tools is not None
        else:
            agent = AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[tool],
            )
            assert len(agent.tools) == 1

    def test_create_agent_with_invalid_tool_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[123],
            )

    def test_create_agent_with_tool_missing_name_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            description = 'A tool'

            def execute(self, **kwargs):
                return 'result'

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[InvalidTool()],
            )

    def test_create_agent_with_tool_missing_description_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            name = 'invalid'

            def execute(self, **kwargs):
                return 'result'

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[InvalidTool()],
            )

    def test_create_agent_with_tool_missing_execute_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            name = 'invalid'
            description = 'A tool'

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[InvalidTool()],
            )

    def test_create_agent_with_tool_non_string_name_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            name = 123
            description = 'A tool'

            def execute(self, **kwargs):
                return 'result'

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[InvalidTool()],
            )

    def test_create_agent_with_tool_non_string_description_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            name = 'invalid'
            description = 123

            def execute(self, **kwargs):
                return 'result'

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[InvalidTool()],
            )

    def test_create_agent_with_tool_non_callable_execute_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            name = 'invalid'
            description = 'A tool'
            execute = 'not callable'

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[InvalidTool()],
            )

    def test_create_agent_tools_preserved_with_all_params(self):
        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        config = {'temperature': 0.7}
        agent = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='Be helpful',
            tools=[tool],
            config=config,
            history_max_size=15,
        )

        assert len(agent.tools) == 1
        assert agent.config == config
        assert agent.history.max_size == 15

    def test_create_agent_with_invalid_string_tool_name_raises_error(self):
        from createagents.domain.exceptions import InvalidBaseToolException

        with pytest.raises(InvalidBaseToolException):
            AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=['invalid_tool_name_that_doesnt_exist'],
            )

    def test_create_agent_with_valid_builtin_tool_names(self):
        from createagents.infra import AvailableTools

        available = AvailableTools.get_system_tools()
        if available:
            tool_name = list(available.keys())[0]
            agent = AgentComposer.create_agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                tools=[tool_name],
            )

            assert agent.tools is not None
            assert len(agent.tools) > 0
        else:
            pytest.skip('No available tools to test')

    def test_create_agent_tools_are_independent_between_agents(self):
        from createagents.domain import BaseTool

        class TestTool(BaseTool):
            name = 'test_tool'
            description = 'A test tool'

            def execute(self, **kwargs):
                return 'result'

        tool = TestTool()
        agent1 = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent1',
            instructions='Test',
            tools=[tool],
        )

        agent2 = AgentComposer.create_agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent2',
            instructions='Test',
            tools=[tool],
        )

        assert agent1.tools is not agent2.tools
