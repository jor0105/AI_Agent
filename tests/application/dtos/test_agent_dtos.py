"""
Testes unitários para os DTOs da aplicação.

Testa validação e conversão de Data Transfer Objects.
"""

import pytest

from src.application.dtos.agent_dtos import (
    AgentConfigOutputDTO,
    ChatInputDTO,
    ChatOutputDTO,
    CreateAgentInputDTO,
)


@pytest.mark.unit
class TestCreateAgentInputDTO:
    """Testes para CreateAgentInputDTO."""

    def test_create_with_valid_data(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="Be helpful",
        )

        assert dto.provider == "openai"
        assert dto.model == "gpt-5-nano"
        assert dto.name == "Test Agent"
        assert dto.instructions == "Be helpful"

    def test_create_with_ollama_provider(self):
        dto = CreateAgentInputDTO(
            provider="ollama",
            model="phi4-mini:latest",
            name="Local Agent",
            instructions="Test",
        )

        assert dto.provider == "ollama"

    def test_validate_success(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test instructions",
        )

        dto.validate()

    def test_validate_empty_model(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="", name="Test", instructions="Test"
        )

        with pytest.raises(ValueError, match="'model'.*obrigatório"):
            dto.validate()

    def test_validate_whitespace_model(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="   ", name="Test", instructions="Test"
        )

        with pytest.raises(ValueError, match="'model'.*obrigatório"):
            dto.validate()

    def test_validate_empty_name(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="", instructions="Test"
        )

        with pytest.raises(ValueError, match="'name'.*obrigatório"):
            dto.validate()

    def test_validate_whitespace_name(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="   ", instructions="Test"
        )

        with pytest.raises(ValueError, match="'name'.*obrigatório"):
            dto.validate()

    def test_validate_empty_instructions(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="Test", instructions=""
        )

        with pytest.raises(ValueError, match="'instructions'.*obrigatório"):
            dto.validate()

    def test_validate_whitespace_instructions(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="Test", instructions="   "
        )

        with pytest.raises(ValueError, match="'instructions'.*obrigatório"):
            dto.validate()

    def test_validate_all_fields_valid(self):
        dto = CreateAgentInputDTO(
            provider="ollama",
            model="phi4-mini:latest",
            name="Production Agent",
            instructions="Detailed instructions here",
        )

        dto.validate()

    def test_validate_invalid_provider(self):
        """Testa validação de provider inválido."""
        dto = CreateAgentInputDTO(
            provider="invalid",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="provider.*deve ser 'openai' ou 'ollama'"):
            dto.validate()

    def test_create_with_history_max_size(self):
        """Testa criação com history_max_size customizado."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=20,
        )

        assert dto.history_max_size == 20

    def test_default_history_max_size(self):
        """Testa valor padrão de history_max_size."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        assert dto.history_max_size == 10

    def test_validate_invalid_history_max_size(self):
        """Testa validação de history_max_size inválido."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=0,
        )

        with pytest.raises(ValueError, match="history_max_size.*maior que zero"):
            dto.validate()

    def test_validate_negative_history_max_size(self):
        """Testa validação de history_max_size negativo."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=-5,
        )

        with pytest.raises(ValueError, match="history_max_size.*maior que zero"):
            dto.validate()


@pytest.mark.unit
class TestAgentConfigOutputDTO:
    """Testes para AgentConfigOutputDTO."""

    def test_create_with_all_fields(self):
        dto = AgentConfigOutputDTO(
            provider="openai",
            name="Test Agent",
            model="gpt-5-nano",
            instructions="Be helpful",
            history=[{"role": "user", "content": "Hello"}],
        )

        assert dto.provider == "openai"
        assert dto.name == "Test Agent"
        assert dto.model == "gpt-5-nano"
        assert dto.instructions == "Be helpful"
        assert len(dto.history) == 1

    def test_create_with_ollama_provider(self):
        dto = AgentConfigOutputDTO(
            provider="ollama",
            name="Test",
            model="phi4-mini:latest",
            instructions="Test",
            history=[],
        )

        assert dto.provider == "ollama"

    def test_to_dict_conversion(self):
        dto = AgentConfigOutputDTO(
            provider="ollama",
            name="Test",
            model="phi4-mini:latest",
            instructions="Instructions",
            history=[{"role": "user", "content": "Hi"}],
        )

        result = dto.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["model"] == "phi4-mini:latest"
        assert result["instructions"] == "Instructions"
        assert result["history"] == [{"role": "user", "content": "Hi"}]
        assert result["provider"] == "ollama"

    def test_to_dict_with_empty_history(self):
        dto = AgentConfigOutputDTO(
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test",
            history=[],
        )

        result = dto.to_dict()

        assert result["history"] == []

    def test_to_dict_with_multiple_history_items(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"},
        ]
        dto = AgentConfigOutputDTO(
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test",
            history=history,
        )

        result = dto.to_dict()

        assert len(result["history"]) == 3
        assert result["history"] == history


@pytest.mark.unit
class TestChatInputDTO:
    """Testes para ChatInputDTO."""

    def test_create_with_message(self):
        dto = ChatInputDTO(message="Hello")

        assert dto.message == "Hello"

    def test_validate_success(self):
        dto = ChatInputDTO(message="Valid message")
        dto.validate()

    def test_validate_empty_message(self):
        dto = ChatInputDTO(message="")

        with pytest.raises(ValueError, match="mensagem não pode estar vazia"):
            dto.validate()

    def test_validate_whitespace_message(self):
        dto = ChatInputDTO(message="   ")

        with pytest.raises(ValueError, match="mensagem não pode estar vazia"):
            dto.validate()

    def test_validate_long_message(self):
        long_message = "A" * 10000
        dto = ChatInputDTO(message=long_message)
        dto.validate()

    def test_validate_multiline_message(self):
        multiline = "Line 1\nLine 2\nLine 3"
        dto = ChatInputDTO(message=multiline)

        dto.validate()

    def test_validate_special_characters(self):
        special = "Hello! 你好 🎉"
        dto = ChatInputDTO(message=special)

        dto.validate()

    def test_create_with_temperature(self):
        """Testa criação com temperature."""
        dto = ChatInputDTO(message="Test", temperature=0.7)

        assert dto.temperature == 0.7

    def test_create_with_max_tokens(self):
        """Testa criação com max_tokens."""
        dto = ChatInputDTO(message="Test", max_tokens=100)

        assert dto.max_tokens == 100

    def test_create_with_top_p(self):
        """Testa criação com top_p."""
        dto = ChatInputDTO(message="Test", top_p=0.9)

        assert dto.top_p == 0.9

    def test_create_with_stop(self):
        """Testa criação com stop sequences."""
        dto = ChatInputDTO(message="Test", stop=["STOP", "END"])

        assert dto.stop == ["STOP", "END"]

    def test_validate_temperature_valid_range(self):
        """Testa validação de temperature em range válido."""
        dto = ChatInputDTO(message="Test", temperature=1.0)
        dto.validate()

    def test_validate_temperature_below_zero(self):
        """Testa validação de temperature abaixo de 0."""
        dto = ChatInputDTO(message="Test", temperature=-0.1)

        with pytest.raises(ValueError, match="temperature.*entre 0.0 e 2.0"):
            dto.validate()

    def test_validate_temperature_above_two(self):
        """Testa validação de temperature acima de 2.0."""
        dto = ChatInputDTO(message="Test", temperature=2.1)

        with pytest.raises(ValueError, match="temperature.*entre 0.0 e 2.0"):
            dto.validate()

    def test_validate_max_tokens_positive(self):
        """Testa validação de max_tokens positivo."""
        dto = ChatInputDTO(message="Test", max_tokens=100)
        dto.validate()

    def test_validate_max_tokens_zero(self):
        """Testa validação de max_tokens zero."""
        dto = ChatInputDTO(message="Test", max_tokens=0)

        with pytest.raises(ValueError, match="max_tokens.*maior que zero"):
            dto.validate()

    def test_validate_max_tokens_negative(self):
        """Testa validação de max_tokens negativo."""
        dto = ChatInputDTO(message="Test", max_tokens=-10)

        with pytest.raises(ValueError, match="max_tokens.*maior que zero"):
            dto.validate()

    def test_validate_top_p_valid_range(self):
        """Testa validação de top_p em range válido."""
        dto = ChatInputDTO(message="Test", top_p=0.5)
        dto.validate()

    def test_validate_top_p_below_zero(self):
        """Testa validação de top_p abaixo de 0."""
        dto = ChatInputDTO(message="Test", top_p=-0.1)

        with pytest.raises(ValueError, match="top_p.*entre 0.0 e 1.0"):
            dto.validate()

    def test_validate_top_p_above_one(self):
        """Testa validação de top_p acima de 1.0."""
        dto = ChatInputDTO(message="Test", top_p=1.1)

        with pytest.raises(ValueError, match="top_p.*entre 0.0 e 1.0"):
            dto.validate()

    def test_validate_all_generation_params(self):
        """Testa validação com todos os parâmetros de geração."""
        dto = ChatInputDTO(
            message="Test", temperature=0.8, max_tokens=200, top_p=0.95, stop=["END"]
        )
        dto.validate()


@pytest.mark.unit
class TestChatOutputDTO:
    """Testes para ChatOutputDTO."""

    def test_create_with_response(self):
        dto = ChatOutputDTO(response="AI response")

        assert dto.response == "AI response"

    def test_to_dict_conversion(self):
        dto = ChatOutputDTO(response="Test response")

        result = dto.to_dict()

        assert isinstance(result, dict)
        assert result["response"] == "Test response"

    def test_to_dict_with_empty_response(self):
        dto = ChatOutputDTO(response="")

        result = dto.to_dict()

        assert result["response"] == ""

    def test_to_dict_with_long_response(self):
        long_response = "A" * 10000
        dto = ChatOutputDTO(response=long_response)

        result = dto.to_dict()

        assert result["response"] == long_response

    def test_to_dict_with_multiline_response(self):
        multiline = "Line 1\nLine 2\nLine 3"
        dto = ChatOutputDTO(response=multiline)

        result = dto.to_dict()

        assert result["response"] == multiline


@pytest.mark.unit
class TestDTOsIntegration:
    """Testes de integração entre DTOs."""

    def test_create_agent_to_config_flow(self):
        # Input DTO
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test instructions",
        )
        input_dto.validate()

        # Simula criação de agente e config output
        output_dto = AgentConfigOutputDTO(
            provider=input_dto.provider,
            name=input_dto.name,
            model=input_dto.model,
            instructions=input_dto.instructions,
            history=[],
        )

        assert output_dto.name == input_dto.name
        assert output_dto.model == input_dto.model
        assert output_dto.provider == input_dto.provider

    def test_chat_input_to_output_flow(self):
        input_dto = ChatInputDTO(message="Hello")
        input_dto.validate()

        # Simula resposta
        output_dto = ChatOutputDTO(response="Hi there!")

        assert input_dto.message == "Hello"
        assert output_dto.response == "Hi there!"

    def test_dto_immutability_after_validation(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        original_model = dto.model
        dto.validate()

        assert dto.model == original_model
