import pytest

from src.application.use_cases.get_config_agents import GetAgentConfigUseCase
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

    def test_execute_with_custom_config(self):
        use_case = GetAgentConfigUseCase()
        custom_config = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.9,
        }
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config=custom_config,
        )

        output = use_case.execute(agent)

        assert output.config == custom_config
        assert output.config["temperature"] == 0.7
        assert output.config["max_tokens"] == 1000
        assert output.config["top_p"] == 0.9

    def test_execute_with_empty_config(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Test",
            instructions="Test",
            config={},
        )

        output = use_case.execute(agent)

        assert output.config == {}
        assert isinstance(output.config, dict)

    def test_execute_with_complex_history(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent.add_user_message("Message 1")
        agent.add_assistant_message("Response 1")
        agent.add_user_message("Message 2")
        agent.add_assistant_message("Response 2")
        agent.add_user_message("Message 3")
        agent.add_assistant_message("Response 3")

        output = use_case.execute(agent)

        assert len(output.history) == 6
        assert output.history[0]["role"] == "user"
        assert output.history[1]["role"] == "assistant"
        assert output.history[2]["role"] == "user"
        assert output.history[3]["role"] == "assistant"
        assert output.history[4]["role"] == "user"
        assert output.history[5]["role"] == "assistant"

    def test_execute_to_dict_includes_configs_key(self):
        use_case = GetAgentConfigUseCase()
        custom_config = {"temperature": 0.5}
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config=custom_config,
        )

        output = use_case.execute(agent)
        result = output.to_dict()

        assert "configs" in result
        assert result["configs"] == custom_config

    def test_execute_with_all_config_types(self):
        use_case = GetAgentConfigUseCase()
        complex_config = {
            "temperature": 0.8,
            "max_tokens": 2000,
        }
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Test",
            instructions="Test",
            config=complex_config,
        )

        output = use_case.execute(agent)

        assert output.config == complex_config
        assert isinstance(output.config["temperature"], float)
        assert isinstance(output.config["max_tokens"], int)

    def test_execute_returns_history_as_list_of_dicts(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        agent.add_user_message("Hello")

        output = use_case.execute(agent)

        assert isinstance(output.history, list)
        assert all(isinstance(item, dict) for item in output.history)
        assert all("role" in item and "content" in item for item in output.history)

    def test_execute_with_long_instructions(self):
        use_case = GetAgentConfigUseCase()
        long_instructions = "A" * 1000
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Test",
            instructions=long_instructions,
        )

        output = use_case.execute(agent)

        assert output.instructions == long_instructions
        assert len(output.instructions) == 1000

    def test_execute_with_special_characters_in_fields(self):
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent 🤖",
            instructions="Be helpful! @#$%^&*()",
        )

        output = use_case.execute(agent)

        assert output.name == "Test Agent 🤖"
        assert output.instructions == "Be helpful! @#$%^&*()"

    def test_execute_preserves_history_order(self):
        """Testa se a ordem do histórico é preservada."""
        use_case = GetAgentConfigUseCase()
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        messages = [
            ("user", "First"),
            ("assistant", "Second"),
            ("user", "Third"),
            ("assistant", "Fourth"),
        ]

        for role, content in messages:
            if role == "user":
                agent.add_user_message(content)
            else:
                agent.add_assistant_message(content)

        output = use_case.execute(agent)

        for i, (expected_role, expected_content) in enumerate(messages):
            assert output.history[i]["role"] == expected_role
            assert output.history[i]["content"] == expected_content
