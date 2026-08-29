from collections.abc import Sequence
from typing import Any, cast

import pytest

from createagents.application import CreateAgentInputDTO, CreateAgentUseCase
from createagents.application.interfaces import ToolRegistry
from createagents.domain import (
    Agent,
    BaseTool,
    InvalidAgentConfigException,
    InvalidBaseToolException,
    InvalidConfigTypeException,
    InvalidProviderException,
    UnsupportedConfigException,
)


class StubToolRegistry(ToolRegistry):
    """In-memory `ToolRegistry` so these tests never touch the real catalog."""

    def __init__(self, tools: dict[str, BaseTool] | None = None) -> None:
        self._tools = {
            name.lower(): tool for name, tool in (tools or {}).items()
        }

    def get_system_tools(self) -> dict[str, str]:
        """Return the stubbed tools as `{name: description}`."""
        return {name: tool.description for name, tool in self._tools.items()}

    def get_tool_instance(self, tool_name: str) -> BaseTool | None:
        """Return the stubbed tool registered under `tool_name`, or None."""
        return self._tools.get(tool_name.lower())


@pytest.mark.unit
class TestCreateAgentUseCase:
    def test_execute_with_valid_input(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test Agent',
            instructions='Be helpful',
        )

        agent = use_case.execute(input_dto)

        assert isinstance(agent, Agent)
        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'
        assert agent.name == 'Test Agent'
        assert agent.instructions == 'Be helpful'

    def test_execute_with_ollama_provider(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='ollama',
            model='phi4-mini:latest',
            name='Local Agent',
            instructions='Test',
        )

        agent = use_case.execute(input_dto)

        assert agent.provider == 'ollama'

    def test_execute_with_openai_provider(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-4',
            name='Test',
            instructions='Test',
        )

        agent = use_case.execute(input_dto)
        assert agent.provider == 'openai'

    def test_execute_creates_empty_history(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent = use_case.execute(input_dto)

        assert len(agent.history) == 0

    def test_execute_uses_default_history_max_size(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent = use_case.execute(input_dto)

        assert agent.history.max_size == 10

    def test_execute_with_custom_history_max_size(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            history_max_size=20,
        )

        agent = use_case.execute(input_dto)
        assert agent.history.max_size == 20

    def test_execute_with_empty_config(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent = use_case.execute(input_dto)

        assert agent.config is None or agent.config == {}

    def test_execute_with_valid_config(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        config = {
            'temperature': 0.7,
            'max_tokens': 100,
            'top_p': 0.9,
        }
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config=config,
        )

        agent = use_case.execute(input_dto)

        assert agent.config == config

    def test_execute_preserves_all_input_data(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='ollama',
            model='phi4-mini:latest',
            name='Complex Agent',
            instructions='Detailed instructions here',
        )

        agent = use_case.execute(input_dto)

        assert agent.provider == input_dto.provider
        assert agent.model == input_dto.model
        assert agent.name == input_dto.name
        assert agent.instructions == input_dto.instructions

    def test_execute_multiple_times_creates_different_agents(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        agent1 = use_case.execute(input_dto)
        agent2 = use_case.execute(input_dto)

        assert agent1 is not agent2
        assert agent1.history is not agent2.history

    def test_execute_with_different_models(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        models = ['gpt-5-nano', 'gpt-4', 'phi4-mini:latest']
        providers = ['openai', 'openai', 'ollama']

        for model, provider in zip(models, providers, strict=True):
            input_dto = CreateAgentInputDTO(
                provider=provider,
                model=model,
                name='Test',
                instructions='Test',
            )
            agent = use_case.execute(input_dto)
            assert agent.model == model
            assert agent.provider == provider

    def test_execute_with_empty_model_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='',
            name='Test',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_whitespace_only_model_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='   ',
            name='Test',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_empty_name_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_whitespace_only_name_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='   ',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_empty_instructions_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_whitespace_only_instructions_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='   ',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_none_name(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name=None,
            instructions='Test',
        )

        agent = use_case.execute(input_dto)
        assert agent.name is None

    def test_execute_with_none_instructions(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions=None,
        )

        agent = use_case.execute(input_dto)
        assert agent.instructions is None

    def test_execute_with_both_none(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name=None,
            instructions=None,
        )

        agent = use_case.execute(input_dto)
        assert agent.name is None
        assert agent.instructions is None

    def test_execute_with_only_required_fields(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
        )

        agent = use_case.execute(input_dto)
        assert agent.provider == 'openai'
        assert agent.model == 'gpt-5-nano'
        assert agent.name is None
        assert agent.instructions is None

    def test_execute_with_empty_provider_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_whitespace_only_provider_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='   ',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_error_message_contains_field_name(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='',
            name='Test',
            instructions='Test',
        )

        with pytest.raises(InvalidAgentConfigException) as exc_info:
            use_case.execute(input_dto)

        assert 'input_dto' in str(exc_info.value)

    def test_execute_with_zero_history_max_size_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            history_max_size=0,
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_negative_history_max_size_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            history_max_size=-5,
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_float_history_max_size_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto.history_max_size = cast(int, 5.5)

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_non_dict_config_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto.config = cast(dict[str, Any] | None, 'invalid')

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_list_as_config_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto.config = cast(dict[str, Any] | None, ['invalid'])

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_unsupported_provider_raises_invalid_provider_exception(
        self,
    ):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='unsupported_provider',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        with pytest.raises(InvalidProviderException):
            use_case.execute(input_dto)

    def test_execute_with_invalid_temperature_too_high_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 2.5},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_invalid_temperature_negative_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': -0.5},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_valid_temperature_boundaries_succeeds(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 0.0},
        )
        agent = use_case.execute(input_dto)
        assert agent.config is not None
        assert agent.config['temperature'] == 0.0

        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'temperature': 2.0},
        )
        agent = use_case.execute(input_dto)
        assert agent.config is not None
        assert agent.config['temperature'] == 2.0

    def test_execute_with_invalid_max_tokens_zero_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'max_tokens': 0},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_invalid_max_tokens_negative_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'max_tokens': -100},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_invalid_max_tokens_float_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'max_tokens': 100.5},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_valid_max_tokens_succeeds(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'max_tokens': 500},
        )

        agent = use_case.execute(input_dto)
        assert agent.config is not None
        assert agent.config['max_tokens'] == 500

    def test_execute_with_invalid_top_p_too_high_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_p': 1.5},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_invalid_top_p_negative_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_p': -0.5},
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_valid_top_p_boundaries_succeeds(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())

        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_p': 0.0},
        )
        agent = use_case.execute(input_dto)
        assert agent.config is not None
        assert agent.config['top_p'] == 0.0

        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'top_p': 1.0},
        )
        agent = use_case.execute(input_dto)
        assert agent.config is not None
        assert agent.config['top_p'] == 1.0

    def test_execute_with_unsupported_config_key_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            config={'unsupported_key': 'value'},
        )

        with pytest.raises(UnsupportedConfigException):
            use_case.execute(input_dto)

    def test_execute_with_invalid_config_type_raises_error(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto.config = {'temperature': object()}

        with pytest.raises(InvalidConfigTypeException):
            use_case.execute(input_dto)

    def test_execute_with_all_valid_configs_combined(self):
        use_case = CreateAgentUseCase(tool_registry=StubToolRegistry())
        input_dto = CreateAgentInputDTO(
            provider='openai',
            model='gpt-4',
            name='Advanced Agent',
            instructions='You are an advanced AI assistant',
            config={
                'temperature': 0.8,
                'max_tokens': 2000,
                'top_p': 0.95,
            },
            history_max_size=50,
        )

        agent = use_case.execute(input_dto)

        assert agent.provider == 'openai'
        assert agent.model == 'gpt-4'
        assert agent.name == 'Advanced Agent'
        assert agent.instructions == 'You are an advanced AI assistant'
        assert agent.config is not None
        assert agent.config['temperature'] == 0.8
        assert agent.config['max_tokens'] == 2000
        assert agent.config['top_p'] == 0.95
        assert agent.history.max_size == 50
        assert len(agent.history) == 0


@pytest.mark.unit
class TestCreateAgentUseCaseToolResolution:
    """Tool names become instances here, using the injected registry."""

    @staticmethod
    def _tool(
        name: str = 'web_search',
        description: str = 'Searches the web',
    ) -> BaseTool:
        class _Tool(BaseTool):
            def execute(self, *args: object, **kwargs: object) -> str:
                return 'result'

        tool = _Tool()
        tool.name = name
        tool.description = description
        return tool

    def _use_case(
        self, tools: dict[str, BaseTool] | None = None
    ) -> CreateAgentUseCase:
        return CreateAgentUseCase(tool_registry=StubToolRegistry(tools))

    def _dto(
        self, tools: Sequence[str | BaseTool] | None
    ) -> CreateAgentInputDTO:
        return CreateAgentInputDTO(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            tools=tools,
        )

    def test_registered_name_resolves_to_the_instance(self):
        tool = self._tool()
        use_case = self._use_case({'web_search': tool})

        agent = use_case.execute(self._dto(['web_search']))

        assert agent.tools == [tool]

    def test_name_lookup_is_case_insensitive(self):
        tool = self._tool()
        use_case = self._use_case({'web_search': tool})

        agent = use_case.execute(self._dto(['Web_Search']))

        assert agent.tools == [tool]

    def test_unregistered_name_raises(self):
        use_case = self._use_case()

        with pytest.raises(InvalidBaseToolException):
            use_case.execute(self._dto(['not_registered']))

    def test_instances_pass_through_untouched(self):
        custom = self._tool(name='custom', description='A custom tool')
        use_case = self._use_case()

        agent = use_case.execute(self._dto([custom]))

        assert agent.tools == [custom]

    def test_names_and_instances_can_be_mixed(self):
        registered = self._tool()
        custom = self._tool(name='custom', description='A custom tool')
        use_case = self._use_case({'web_search': registered})

        agent = use_case.execute(self._dto([custom, 'web_search']))

        assert agent.tools == [custom, registered]

    def test_no_tools_yields_none(self):
        use_case = self._use_case()

        agent = use_case.execute(self._dto(None))

        assert agent.tools is None
