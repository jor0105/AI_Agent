import pytest

from src.domain.entities.agent_domain import Agent
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
