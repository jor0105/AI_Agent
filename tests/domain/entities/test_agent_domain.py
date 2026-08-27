import pytest

from createagents.domain import (
    Agent,
    History,
    InvalidAgentConfigException,
    InvalidConfigTypeException,
    InvalidProviderException,
    MessageRole,
    UnsupportedConfigException,
)


@pytest.mark.unit
class TestAgent:
    def test_create_agent_with_required_fields(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='You are a helpful assistant',
        )

        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'
        assert agent.name == 'Test Agent'
        assert agent.instructions == 'You are a helpful assistant'
        assert isinstance(agent.history, History)

    def test_create_agent_with_ollama_provider(self):
        agent = Agent(
            provider='ollama',
            model='phi4-mini:latest',
            name='Local Agent',
            instructions='Test',
        )

        assert agent.provider == 'ollama'

    def test_agent_history_starts_empty(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert len(agent.history) == 0
        assert bool(agent.history) is False

    def test_agent_history_is_history_object(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert isinstance(agent.history, History)

    def test_add_user_message(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_user_message('Hello')

        assert len(agent.history) == 1
        messages = agent.history.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == 'Hello'

    def test_add_assistant_message(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_assistant_message('Hi there!')

        assert len(agent.history) == 1
        messages = agent.history.get_messages()
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == 'Hi there!'

    def test_add_multiple_messages(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_user_message('Question 1')
        agent.add_assistant_message('Answer 1')
        agent.add_user_message('Question 2')
        agent.add_assistant_message('Answer 2')

        assert len(agent.history) == 4

    def test_clear_history(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        agent.add_user_message('Test message')

        assert len(agent.history) == 1

        agent.clear_history()

        assert len(agent.history) == 0

    def test_agent_preserves_conversation_flow(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_user_message('Hello')
        agent.add_assistant_message('Hi!')
        agent.add_user_message('How are you?')
        agent.add_assistant_message("I'm good!")

        messages = agent.history.get_messages()

        assert messages[0].role == MessageRole.USER
        assert messages[0].content == 'Hello'
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == 'Hi!'
        assert messages[2].role == MessageRole.USER
        assert messages[2].content == 'How are you?'
        assert messages[3].role == MessageRole.ASSISTANT
        assert messages[3].content == "I'm good!"

    def test_agent_with_different_models(self):
        models = [
            'gpt-5-nano',
            'gpt-5-nano',
            'phi4-mini:latest',
            'phi4-mini:latest',
        ]
        providers = ['openai', 'openai', 'ollama', 'ollama']

        for model, provider in zip(models, providers, strict=True):
            agent = Agent(
                provider=provider,
                model=model,
                name='Test',
                instructions='Test',
            )
            assert agent.model == model
            assert agent.provider == provider

    def test_agent_identity_fields_are_accessible(self):
        agent = Agent(
            provider='ollama',
            model='phi4-mini:latest',
            name='My Agent',
            instructions='Be helpful',
        )

        assert agent.provider == 'ollama'
        assert agent.model == 'phi4-mini:latest'
        assert agent.name == 'My Agent'
        assert agent.instructions == 'Be helpful'

    def test_agent_can_be_modified(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.name = 'Updated Name'
        agent.model = 'gpt-4'
        agent.provider = 'ollama'

        assert agent.name == 'Updated Name'
        assert agent.model == 'gpt-4'
        assert agent.provider == 'ollama'

    def test_agent_history_respects_max_size(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        for i in range(15):
            agent.add_user_message(f'Message {i}')

        assert len(agent.history) == 10
        messages = agent.history.get_messages()
        assert messages[0].content == 'Message 5'
        assert messages[-1].content == 'Message 14'

    def test_multiple_agents_have_independent_histories(self):
        agent1 = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent1',
            instructions='Test',
        )
        agent2 = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Agent2',
            instructions='Test',
        )

        agent1.add_user_message('Message for agent1')
        agent2.add_user_message('Message for agent2')

        assert len(agent1.history) == 1
        assert len(agent2.history) == 1
        assert agent1.history.get_messages()[0].content == 'Message for agent1'
        assert agent2.history.get_messages()[0].content == 'Message for agent2'

    def test_agent_with_long_instructions(self):
        long_instructions = 'A' * 10000
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions=long_instructions,
        )

        assert agent.instructions == long_instructions
        assert len(agent.instructions) == 10000

    def test_agent_with_special_characters_in_fields(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test Agent 🤖',
            instructions='You are helpful! 😊',
        )

        assert '🤖' in agent.name
        assert '😊' in agent.instructions

    def test_agent_with_multiline_instructions(self):
        multiline_instructions = """
        You are a helpful assistant.
        Follow these rules:
        1. Be polite
        2. Be concise
        3. Be accurate
        """
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions=multiline_instructions,
        )

        assert '\n' in agent.instructions
        assert 'Be polite' in agent.instructions

    def test_agent_dataclass_fields(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert hasattr(agent, '__dataclass_fields__')

        fields = agent.__dataclass_fields__
        assert 'provider' in fields
        assert 'model' in fields
        assert 'name' in fields
        assert 'instructions' in fields
        assert 'history' in fields

    def test_agent_with_invalid_provider(self):
        with pytest.raises(
            InvalidProviderException,
            match="Provider 'invalido' is not available",
        ):
            Agent(
                provider='invalido',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
            )

    def test_agent_with_valid_config(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.7, 'max_tokens': 100, 'top_p': 0.9},
        )

        assert agent.config['temperature'] == 0.7
        assert agent.config['max_tokens'] == 100
        assert agent.config['top_p'] == 0.9

    def test_agent_with_empty_config(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={},
        )

        assert agent.config == {}

    def test_agent_config_defaults_to_empty_dict(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert agent.config is None or agent.config == {}
        assert isinstance(agent.config, (dict, type(None)))

    def test_agent_with_unsupported_config(self):
        with pytest.raises(
            UnsupportedConfigException, match='is not supported'
        ):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'invalid_config': 123},
            )

    def test_agent_with_invalid_config_type(self):
        with pytest.raises(
            InvalidConfigTypeException, match='has invalid type'
        ):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'temperature': object()},
            )

    def test_agent_with_invalid_temperature_value(self):
        with pytest.raises(InvalidAgentConfigException, match='temperature'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'temperature': 3.0},
            )

    def test_agent_with_invalid_max_tokens_value(self):
        with pytest.raises(InvalidAgentConfigException, match='max_tokens'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'max_tokens': -10},
            )

    def test_agent_with_invalid_max_tokens_type(self):
        with pytest.raises(InvalidAgentConfigException, match='max_tokens'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'max_tokens': '100'},
            )

    def test_agent_with_invalid_top_p_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_p'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'top_p': 1.5},
            )

    def test_agent_with_multiple_configs(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.8, 'max_tokens': 500, 'top_p': 0.95},
        )

        assert len(agent.config) == 3
        assert agent.config['temperature'] == 0.8
        assert agent.config['max_tokens'] == 500
        assert agent.config['top_p'] == 0.95

    def test_agent_with_partial_config(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.5},
        )

        assert len(agent.config) == 1
        assert agent.config['temperature'] == 0.5

    def test_agent_config_with_none_values(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': None, 'max_tokens': None},
        )

        assert agent.config['temperature'] is None
        assert agent.config['max_tokens'] is None

    def test_agent_provider_case_insensitive(self):
        agent = Agent(
            provider='OpenAI',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert agent.provider == 'OpenAI'

    def test_agent_with_boundary_temperature_values(self):
        agent_min = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.0},
        )
        assert agent_min.config['temperature'] == 0.0

        agent_max = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 2.0},
        )
        assert agent_max.config['temperature'] == 2.0

    def test_agent_with_boundary_top_p_values(self):
        agent_min = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_p': 0.0},
        )
        assert agent_min.config['top_p'] == 0.0

        agent_max = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_p': 1.0},
        )
        assert agent_max.config['top_p'] == 1.0

    def test_agent_with_minimum_valid_max_tokens(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'max_tokens': 1},
        )
        assert agent.config['max_tokens'] == 1

    def test_agent_with_none_optional_fields(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name=None,
            instructions=None,
        )
        assert agent.name is None
        assert agent.instructions is None
        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'

    def test_agent_config_with_list_values(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.5},
        )
        assert agent.config['temperature'] == 0.5

    def test_agent_config_with_boolean_values(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.5},
        )
        assert isinstance(agent.config['temperature'], float)

    def test_agent_with_top_p_below_min(self):
        with pytest.raises(InvalidAgentConfigException, match='top_p'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'top_p': -0.1},
            )

    def test_agent_with_top_p_above_max(self):
        with pytest.raises(InvalidAgentConfigException, match='top_p'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'top_p': 1.1},
            )

    def test_agent_with_max_tokens_as_string(self):
        with pytest.raises(InvalidAgentConfigException, match='max_tokens'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'max_tokens': '100'},
            )

    def test_agent_config_with_mixed_valid_configs(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={
                'temperature': 1.5,
                'max_tokens': 2048,
                'top_p': 0.95,
            },
        )
        assert agent.config['temperature'] == 1.5
        assert agent.config['max_tokens'] == 2048
        assert agent.config['top_p'] == 0.95

    def test_agent_config_scenarios_think_accepts_boolean_and_string(self):
        agent_bool = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'think': True},
        )
        assert agent_bool.config['think'] is True

        agent_str = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'think': 'medium'},
        )
        assert agent_str.config['think'] == 'medium'

    def test_agent_config_scenarios_think_invalid_type(self):
        with pytest.raises(InvalidAgentConfigException, match='think'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'think': 123},
            )

    def test_agent_config_scenarios_top_k_accepts_positive_integer(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_k': 25},
        )
        assert agent.config['top_k'] == 25

    def test_agent_config_scenarios_top_k_invalid_value(self):
        with pytest.raises(InvalidAgentConfigException, match='top_k'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'top_k': 0},
            )

    def test_agent_config_scenarios_stream_accepts_boolean(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'stream': True},
        )
        assert agent.config['stream'] is True

    def test_agent_config_scenarios_stream_rejects_non_boolean(self):
        with pytest.raises(InvalidAgentConfigException, match='stream'):
            Agent(
                provider='openai',
                model='gpt-5-nano',
                name='Test',
                instructions='Test',
                config={'stream': 'yes'},
            )

    def test_agent_history_initial_state(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        assert len(agent.history) == 0
        assert isinstance(agent.history, History)
        assert agent.history.max_size == 10

    def test_agent_add_messages_alternating(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        agent.add_user_message('Q1')
        agent.add_assistant_message('A1')
        agent.add_user_message('Q2')
        agent.add_assistant_message('A2')

        messages = agent.history.get_messages()
        assert len(messages) == 4
        assert messages[0].content == 'Q1'
        assert messages[1].content == 'A1'
        assert messages[2].content == 'Q2'
        assert messages[3].content == 'A2'


@pytest.mark.unit
class TestAgentToolMessages:
    def test_add_tool_message(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_tool_message('Tool executed successfully')

        assert len(agent.history) == 1
        messages = agent.history.get_messages()
        assert messages[0].role == MessageRole.TOOL
        assert messages[0].content == 'Tool executed successfully'

    def test_add_multiple_tool_messages(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_tool_message('Tool 1 result')
        agent.add_tool_message('Tool 2 result')
        agent.add_tool_message('Tool 3 result')

        assert len(agent.history) == 3
        messages = agent.history.get_messages()
        for msg in messages:
            assert msg.role == MessageRole.TOOL

    def test_add_tool_message_with_json_content(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        json_result = '{"status": "success", "data": [1, 2, 3]}'
        agent.add_tool_message(json_result)

        messages = agent.history.get_messages()
        assert messages[0].content == json_result
        assert '{' in messages[0].content

    def test_add_tool_message_with_error_content(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        error_msg = 'Error: Tool execution failed - Connection timeout'
        agent.add_tool_message(error_msg)

        messages = agent.history.get_messages()
        assert messages[0].role == MessageRole.TOOL
        assert 'Error' in messages[0].content

    def test_conversation_with_tool_messages(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent.add_user_message("What's the weather in Tokyo?")
        agent.add_tool_message(
            '{"city": "Tokyo", "temp": 22, "conditions": "Sunny"}'
        )
        agent.add_assistant_message('The weather in Tokyo is sunny with 22°C.')

        messages = agent.history.get_messages()
        assert len(messages) == 3
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.TOOL
        assert messages[2].role == MessageRole.ASSISTANT

    def test_tool_message_in_history_respects_max_size(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        for i in range(15):
            if i % 3 == 0:
                agent.add_user_message(f'User {i}')
            elif i % 3 == 1:
                agent.add_tool_message(f'Tool {i}')
            else:
                agent.add_assistant_message(f'Assistant {i}')

        assert len(agent.history) == 10

    def test_add_tool_message_with_special_characters(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        special_content = 'Result: 你好 🎉 @#$%^&*()'
        agent.add_tool_message(special_content)

        messages = agent.history.get_messages()
        assert '你好' in messages[0].content
        assert '🎉' in messages[0].content

    def test_add_tool_message_with_multiline_content(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        multiline = 'Line 1: Result\nLine 2: Details\nLine 3: Summary'
        agent.add_tool_message(multiline)

        messages = agent.history.get_messages()
        assert '\n' in messages[0].content
        assert messages[0].content.count('\n') == 2


@pytest.mark.unit
class TestAgentWithTools:
    def test_agent_with_tools_attribute(self):
        from createagents.domain.value_objects import BaseTool

        class MockTool(BaseTool):
            name = 'mock_tool'
            description = 'A mock tool'

            def execute(self) -> str:
                return 'mock result'

        tool = MockTool()
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=[tool],
        )

        assert agent.tools is not None
        assert len(agent.tools) == 1
        assert agent.tools[0].name == 'mock_tool'

    def test_agent_without_tools(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        assert agent.tools is None

    def test_agent_with_empty_tools_list(self):
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=[],
        )

        assert agent.tools == []
        assert isinstance(agent.tools, list)

    def test_agent_with_multiple_tools(self):
        from createagents.domain.value_objects import BaseTool

        class Tool1(BaseTool):
            name = 'tool1'
            description = 'First tool'

            def execute(self) -> str:
                return 'result1'

        class Tool2(BaseTool):
            name = 'tool2'
            description = 'Second tool'

            def execute(self) -> str:
                return 'result2'

        tools = [Tool1(), Tool2()]
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=tools,
        )

        assert len(agent.tools) == 2
        assert agent.tools[0].name == 'tool1'
        assert agent.tools[1].name == 'tool2'
