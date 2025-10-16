import pytest

from src.domain.entities.agent_domain import Agent
from src.domain.exceptions.domain_exceptions import (
    InvalidAgentConfigException,
    InvalidConfigTypeException,
    InvalidProviderException,
    UnsupportedConfigException,
)
from src.domain.value_objects import History, MessageRole


@pytest.mark.unit
class TestAgent:
    def test_create_agent_with_required_fields(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="You are a helpful assistant",
        )

        assert agent.provider == "openai"
        assert agent.model == "gpt-5-nano"
        assert agent.name == "Test Agent"
        assert agent.instructions == "You are a helpful assistant"
        assert isinstance(agent.history, History)

    def test_create_agent_with_ollama_provider(self):
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Local Agent",
            instructions="Test",
        )

        assert agent.provider == "ollama"

    def test_agent_history_starts_empty(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert len(agent.history) == 0
        assert bool(agent.history) is False

    def test_agent_history_is_history_object(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert isinstance(agent.history, History)

    def test_add_user_message(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent.add_user_message("Hello")

        assert len(agent.history) == 1
        messages = agent.history.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"

    def test_add_assistant_message(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent.add_assistant_message("Hi there!")

        assert len(agent.history) == 1
        messages = agent.history.get_messages()
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == "Hi there!"

    def test_add_multiple_messages(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent.add_user_message("Question 1")
        agent.add_assistant_message("Answer 1")
        agent.add_user_message("Question 2")
        agent.add_assistant_message("Answer 2")

        assert len(agent.history) == 4

    def test_clear_history(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        agent.add_user_message("Test message")

        assert len(agent.history) == 1

        agent.clear_history()

        assert len(agent.history) == 0

    def test_agent_preserves_conversation_flow(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent.add_user_message("Hello")
        agent.add_assistant_message("Hi!")
        agent.add_user_message("How are you?")
        agent.add_assistant_message("I'm good!")

        messages = agent.history.get_messages()

        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hi!"
        assert messages[2].role == MessageRole.USER
        assert messages[2].content == "How are you?"
        assert messages[3].role == MessageRole.ASSISTANT
        assert messages[3].content == "I'm good!"

    def test_agent_with_different_models(self):
        models = ["gpt-5-nano", "gpt-5-nano", "phi4-mini:latest", "phi4-mini:latest"]
        providers = ["openai", "openai", "ollama", "ollama"]

        for model, provider in zip(models, providers):
            agent = Agent(
                provider=provider, model=model, name="Test", instructions="Test"
            )
            assert agent.model == model
            assert agent.provider == provider

    def test_agent_identity_fields_are_accessible(self):
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="My Agent",
            instructions="Be helpful",
        )

        assert agent.provider == "ollama"
        assert agent.model == "phi4-mini:latest"
        assert agent.name == "My Agent"
        assert agent.instructions == "Be helpful"

    def test_agent_can_be_modified(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent.name = "Updated Name"
        agent.model = "gpt-4"
        agent.provider = "ollama"

        assert agent.name == "Updated Name"
        assert agent.model == "gpt-4"
        assert agent.provider == "ollama"

    def test_agent_history_respects_max_size(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        for i in range(15):
            agent.add_user_message(f"Message {i}")

        assert len(agent.history) == 10
        messages = agent.history.get_messages()
        assert messages[0].content == "Message 5"
        assert messages[-1].content == "Message 14"

    def test_multiple_agents_have_independent_histories(self):
        agent1 = Agent(
            provider="openai", model="gpt-5-nano", name="Agent1", instructions="Test"
        )
        agent2 = Agent(
            provider="openai", model="gpt-5-nano", name="Agent2", instructions="Test"
        )

        agent1.add_user_message("Message for agent1")
        agent2.add_user_message("Message for agent2")

        assert len(agent1.history) == 1
        assert len(agent2.history) == 1
        assert agent1.history.get_messages()[0].content == "Message for agent1"
        assert agent2.history.get_messages()[0].content == "Message for agent2"

    def test_agent_with_long_instructions(self):
        long_instructions = "A" * 10000
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions=long_instructions,
        )

        assert agent.instructions == long_instructions
        assert len(agent.instructions) == 10000

    def test_agent_with_special_characters_in_fields(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent 🤖",
            instructions="You are helpful! 😊",
        )

        assert "🤖" in agent.name
        assert "😊" in agent.instructions

    def test_agent_with_multiline_instructions(self):
        multiline_instructions = """
        You are a helpful assistant.
        Follow these rules:
        1. Be polite
        2. Be concise
        3. Be accurate
        """
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions=multiline_instructions,
        )

        assert "\n" in agent.instructions
        assert "Be polite" in agent.instructions

    def test_agent_dataclass_fields(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert hasattr(agent, "__dataclass_fields__")

        # Verifica campos obrigatórios
        fields = agent.__dataclass_fields__
        assert "provider" in fields
        assert "model" in fields
        assert "name" in fields
        assert "instructions" in fields
        assert "history" in fields

    def test_agent_with_invalid_provider(self):
        with pytest.raises(
            InvalidProviderException, match="provider.*não está disponível"
        ):
            Agent(
                provider="invalido",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
            )

    def test_agent_with_valid_config(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 0.7, "max_tokens": 100, "top_p": 0.9},
        )

        assert agent.config["temperature"] == 0.7
        assert agent.config["max_tokens"] == 100
        assert agent.config["top_p"] == 0.9

    def test_agent_with_empty_config(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={},
        )

        assert agent.config == {}

    def test_agent_config_defaults_to_empty_dict(self):
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert agent.config == {}
        assert isinstance(agent.config, dict)

    def test_agent_with_unsupported_config(self):
        with pytest.raises(UnsupportedConfigException, match="não é suportada"):
            Agent(
                provider="openai",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
                config={"invalid_config": 123},
            )

    def test_agent_with_invalid_config_type(self):
        with pytest.raises(InvalidConfigTypeException, match="tipo inválido"):
            Agent(
                provider="openai",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
                config={"temperature": object()},
            )

    def test_agent_with_invalid_temperature_value(self):
        with pytest.raises(InvalidAgentConfigException, match="temperature"):
            Agent(
                provider="openai",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
                config={"temperature": 3.0},  # Fora do intervalo 0.0-2.0
            )

    def test_agent_with_invalid_max_tokens_value(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            Agent(
                provider="openai",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
                config={"max_tokens": -10},  # Valor negativo
            )

    def test_agent_with_invalid_max_tokens_type(self):
        with pytest.raises(InvalidAgentConfigException, match="max_tokens"):
            Agent(
                provider="openai",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
                config={"max_tokens": "100"},  # String em vez de int
            )

    def test_agent_with_invalid_top_p_value(self):
        with pytest.raises(InvalidAgentConfigException, match="top_p"):
            Agent(
                provider="openai",
                model="gpt-5-nano",
                name="Test",
                instructions="Test",
                config={"top_p": 1.5},  # Fora do intervalo 0.0-1.0
            )

    def test_agent_with_multiple_configs(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 0.8, "max_tokens": 500, "top_p": 0.95},
        )

        assert len(agent.config) == 3
        assert agent.config["temperature"] == 0.8
        assert agent.config["max_tokens"] == 500
        assert agent.config["top_p"] == 0.95

    def test_agent_with_partial_config(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 0.5},
        )

        assert len(agent.config) == 1
        assert agent.config["temperature"] == 0.5

    def test_agent_config_with_none_values(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": None, "max_tokens": None},
        )

        assert agent.config["temperature"] is None
        assert agent.config["max_tokens"] is None

    def test_agent_provider_case_insensitive(self):
        agent = Agent(
            provider="OpenAI", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert agent.provider == "OpenAI"

    def test_agent_with_boundary_temperature_values(self):
        # Temperatura mínima válida
        agent_min = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 0.0},
        )
        assert agent_min.config["temperature"] == 0.0

        # Temperatura máxima válida
        agent_max = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 2.0},
        )
        assert agent_max.config["temperature"] == 2.0

    def test_agent_with_boundary_top_p_values(self):
        # top_p mínimo válido
        agent_min = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"top_p": 0.0},
        )
        assert agent_min.config["top_p"] == 0.0

        # top_p máximo válido
        agent_max = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"top_p": 1.0},
        )
        assert agent_max.config["top_p"] == 1.0

    def test_agent_with_minimum_valid_max_tokens(self):
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"max_tokens": 1},
        )
        assert agent.config["max_tokens"] == 1
