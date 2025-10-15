import pytest

from src.application.use_cases.get_config_new_agents import GetAgentConfigUseCase
from src.domain.entities.agent_domain import Agent


@pytest.mark.unit
class TestGetAgentConfigUseCase:
    def test_execute_returns_correct_dto(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Test Agent",
            instructions="Be helpful",
        )

        output = use_case.execute(agent)

        assert output.name == "Test Agent"
        assert output.model == "phi4-mini:latest"
        assert output.instructions == "Be helpful"
        assert output.provider == "ollama"

    def test_execute_with_empty_history(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        output = use_case.execute(agent)

        assert output.history == []

    def test_execute_with_history(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        agent.add_user_message("Hello")
        agent.add_assistant_message("Hi")

        output = use_case.execute(agent)

        assert len(output.history) == 2
        assert output.history[0] == {"role": "user", "content": "Hello"}
        assert output.history[1] == {"role": "assistant", "content": "Hi"}

    def test_execute_with_openai_provider(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        output = use_case.execute(agent)

        assert output.provider == "openai"

    def test_execute_preserves_all_fields(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="My Agent",
            instructions="Complex instructions",
        )
        agent.add_user_message("Message 1")
        agent.add_assistant_message("Response 1")

        output = use_case.execute(agent)

        assert output.provider == agent.provider
        assert output.model == agent.model
        assert output.name == agent.name
        assert output.instructions == agent.instructions
        assert len(output.history) == 2

    def test_execute_to_dict_conversion(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        output = use_case.execute(agent)
        result = output.to_dict()

        assert isinstance(result, dict)
        assert "name" in result
        assert "model" in result
        assert "instructions" in result
        assert "history" in result
        assert "provider" in result

    def test_execute_multiple_times_returns_current_state(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        output1 = use_case.execute(agent)
        assert len(output1.history) == 0

        agent.add_user_message("New message")

        output2 = use_case.execute(agent)
        assert len(output2.history) == 1

    def test_execute_does_not_modify_agent(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        agent.add_user_message("Test")

        original_history_len = len(agent.history)
        use_case.execute(agent)

        assert len(agent.history) == original_history_len
