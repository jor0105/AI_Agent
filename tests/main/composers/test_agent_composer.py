import pytest

from src.application.use_cases.chat_with_agent import ChatWithAgentUseCase
from src.application.use_cases.get_config_agents import GetAgentConfigUseCase
from src.domain.entities.agent_domain import Agent
from src.domain.exceptions import InvalidAgentConfigException
from src.main.composers.agent_composer import AgentComposer


@pytest.mark.unit
class TestAgentComposer:
    def test_create_agent_with_valid_data(self):
        agent = AgentComposer.create_agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="Be helpful",
        )

        assert isinstance(agent, Agent)
        assert agent.provider == "openai"
        assert agent.model == "gpt-5-nano"
        assert agent.name == "Test Agent"
        assert agent.instructions == "Be helpful"

    def test_create_agent_with_ollama_provider(self):
        agent = AgentComposer.create_agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Local Agent",
            instructions="Test",
        )

        assert agent.provider == "ollama"

    def test_create_agent_with_empty_model_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider="openai", model="", name="Test", instructions="Test"
            )

    def test_create_agent_with_empty_name_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider="openai", model="gpt-5-nano", name="", instructions="Test"
            )

    def test_create_agent_with_empty_instructions_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider="openai", model="gpt-5-nano", name="Test", instructions=""
            )

    def test_create_chat_use_case_returns_use_case(self):
        use_case = AgentComposer.create_chat_use_case(
            provider="openai", model="gpt-5-nano"
        )

        assert isinstance(use_case, ChatWithAgentUseCase)

    def test_create_chat_use_case_with_ollama_provider(self):
        use_case = AgentComposer.create_chat_use_case(
            provider="ollama", model="phi4-mini:latest"
        )

        assert isinstance(use_case, ChatWithAgentUseCase)

    def test_create_chat_use_case_injects_correct_adapter(self):
        use_case = AgentComposer.create_chat_use_case(
            provider="openai", model="gpt-5-nano"
        )

        assert hasattr(use_case, "_ChatWithAgentUseCase__chat_repository")

    def test_create_get_config_use_case_returns_use_case(self):
        use_case = AgentComposer.create_get_config_use_case()

        assert isinstance(use_case, GetAgentConfigUseCase)

    def test_create_multiple_agents_are_independent(self):
        agent1 = AgentComposer.create_agent(
            provider="openai", model="gpt-5-nano", name="Agent1", instructions="Test1"
        )
        agent2 = AgentComposer.create_agent(
            provider="openai", model="gpt-5-nano", name="Agent2", instructions="Test2"
        )

        assert agent1 is not agent2
        assert agent1.name != agent2.name

    def test_create_multiple_chat_use_cases_are_independent(self):
        use_case1 = AgentComposer.create_chat_use_case(
            provider="openai", model="gpt-5-nano"
        )
        use_case2 = AgentComposer.create_chat_use_case(
            provider="openai", model="gpt-5-nano"
        )

        assert use_case1 is not use_case2

    def test_create_agent_wraps_exceptions_in_invalid_config(self):
        with pytest.raises(InvalidAgentConfigException):
            AgentComposer.create_agent(
                provider="openai", model="gpt-5-nano", name="   ", instructions="Test"
            )

    def test_error_message_contains_composer_context(self):
        try:
            AgentComposer.create_agent(
                provider="openai", model="", name="Test", instructions="Test"
            )
        except InvalidAgentConfigException:
            pass
