"""
Testes unitários para CreateAgentUseCase.

Testa a criação de agentes através do use case.
"""

import pytest

from src.application.dtos import CreateAgentInputDTO
from src.application.use_cases.create_agent import CreateAgentUseCase
from src.domain.entities.agent_domain import Agent
from src.domain.exceptions import InvalidAgentConfigException


@pytest.mark.unit
class TestCreateAgentUseCase:
    """Testes para CreateAgentUseCase."""

    def test_execute_with_valid_input(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="Be helpful",
        )

        agent = use_case.execute(input_dto)

        assert isinstance(agent, Agent)
        assert agent.provider == "openai"
        assert agent.model == "gpt-5-nano"
        assert agent.name == "Test Agent"
        assert agent.instructions == "Be helpful"

    def test_execute_with_ollama_provider(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="ollama",
            model="phi4-mini:latest",
            name="Local Agent",
            instructions="Test",
        )

        agent = use_case.execute(input_dto)

        assert agent.provider == "ollama"

    def test_execute_creates_empty_history(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        agent = use_case.execute(input_dto)

        assert len(agent.history) == 0

    def test_execute_with_empty_model_raises_error(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_empty_name_raises_error(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="",
            instructions="Test",
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_empty_instructions_raises_error(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="",
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_multiple_times_creates_different_agents(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        agent1 = use_case.execute(input_dto)
        agent2 = use_case.execute(input_dto)

        assert agent1 is not agent2
        assert agent1.history is not agent2.history

    def test_execute_with_different_models(self):
        use_case = CreateAgentUseCase()
        models = ["gpt-5-nano", "gpt-5-nano", "phi4-mini:latest"]
        providers = ["openai", "openai", "ollama"]

        for model, provider in zip(models, providers):
            input_dto = CreateAgentInputDTO(
                provider=provider,
                model=model,
                name="Test",
                instructions="Test",
            )
            agent = use_case.execute(input_dto)
            assert agent.model == model
            assert agent.provider == provider

    def test_execute_preserves_all_input_data(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="ollama",
            model="phi4-mini:latest",
            name="Complex Agent",
            instructions="Detailed instructions here",
        )

        agent = use_case.execute(input_dto)

        assert agent.provider == input_dto.provider
        assert agent.model == input_dto.model
        assert agent.name == input_dto.name
        assert agent.instructions == input_dto.instructions

    def test_execute_error_message_contains_field_name(self):
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="",  # inválido
            name="Test",
            instructions="Test",
        )

        with pytest.raises(InvalidAgentConfigException, match="input_dto"):
            use_case.execute(input_dto)

    def test_execute_with_invalid_provider_raises_error(self):
        """Testa que provider inválido levanta exceção."""
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="invalid_provider",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(InvalidAgentConfigException):
            use_case.execute(input_dto)

    def test_execute_with_openai_provider(self):
        """Testa criação com provider openai."""
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-4",
            name="Test",
            instructions="Test",
        )

        agent = use_case.execute(input_dto)
        assert agent.provider == "openai"

    def test_execute_with_custom_history_max_size(self):
        """Testa criação com tamanho customizado de histórico."""
        use_case = CreateAgentUseCase()
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=20,
        )

        agent = use_case.execute(input_dto)
        assert agent.history.MAX_SIZE == 20
