import pytest

from src.application.dtos.agent_dtos import (
    AgentConfigOutputDTO,
    ChatInputDTO,
    ChatOutputDTO,
    CreateAgentInputDTO,
)


@pytest.mark.unit
class TestCreateAgentInputDTO:
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

    def test_validate_with_config(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 0.7, "top_p": 0.9},
        )

        dto.validate()
        assert dto.config == {"temperature": 0.7, "top_p": 0.9}

    def test_validate_empty_config(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        dto.validate()
        assert dto.config == {}

    def test_create_with_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=20,
        )

        assert dto.history_max_size == 20

    def test_default_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        assert dto.history_max_size == 10

    def test_validate_invalid_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=0,
        )

        with pytest.raises(ValueError, match="history_max_size.*inteiro positivo"):
            dto.validate()

    def test_validate_negative_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=-5,
        )

        with pytest.raises(ValueError, match="history_max_size.*inteiro positivo"):
            dto.validate()

    def test_validate_invalid_config_type(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config="invalid",  # type: ignore
        )

        with pytest.raises(ValueError, match="'config'.*dicionário"):
            dto.validate()

    def test_validate_non_int_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size="invalid",  # type: ignore
        )

        with pytest.raises(ValueError, match="history_max_size"):
            dto.validate()

    def test_validate_non_string_provider(self):
        dto = CreateAgentInputDTO(
            provider=123,  # type: ignore
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="'provider'.*obrigatório"):
            dto.validate()

    def test_validate_empty_provider(self):
        dto = CreateAgentInputDTO(
            provider="",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="'provider'.*obrigatório"):
            dto.validate()

    def test_validate_whitespace_provider(self):
        dto = CreateAgentInputDTO(
            provider="   ",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="'provider'.*obrigatório"):
            dto.validate()


@pytest.mark.unit
class TestAgentConfigOutputDTO:
    def test_create_with_all_fields(self):
        dto = AgentConfigOutputDTO(
            provider="openai",
            name="Test Agent",
            model="gpt-5-nano",
            instructions="Be helpful",
            config={"temperature": 0.7},
            history=[{"role": "user", "content": "Hello"}],
        )

        assert dto.provider == "openai"
        assert dto.name == "Test Agent"
        assert dto.model == "gpt-5-nano"
        assert dto.instructions == "Be helpful"
        assert dto.config == {"temperature": 0.7}
        assert len(dto.history) == 1

    def test_create_with_ollama_provider(self):
        dto = AgentConfigOutputDTO(
            provider="ollama",
            name="Test",
            model="phi4-mini:latest",
            instructions="Test",
            config={},
            history=[],
        )

        assert dto.provider == "ollama"

    def test_to_dict_conversion(self):
        dto = AgentConfigOutputDTO(
            provider="ollama",
            name="Test",
            model="phi4-mini:latest",
            instructions="Instructions",
            config={"temperature": 0.8},
            history=[{"role": "user", "content": "Hi"}],
        )

        result = dto.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["model"] == "phi4-mini:latest"
        assert result["instructions"] == "Instructions"
        assert result["history"] == [{"role": "user", "content": "Hi"}]
        assert result["provider"] == "ollama"
        assert result["configs"] == {"temperature": 0.8}

    def test_to_dict_with_empty_history(self):
        dto = AgentConfigOutputDTO(
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test",
            config={},
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
            config={"top_p": 0.9},
            history=history,
        )

        result = dto.to_dict()

        assert len(result["history"]) == 3
        assert result["history"] == history

    def test_to_dict_all_keys_present(self):
        dto = AgentConfigOutputDTO(
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test instructions",
            config={"key": "value"},
            history=[],
        )

        result = dto.to_dict()

        expected_keys = {
            "provider",
            "model",
            "name",
            "instructions",
            "configs",
            "history",
        }
        assert set(result.keys()) == expected_keys

    def test_to_dict_with_complex_config(self):
        complex_config = {
            "temperature": 0.7,
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        dto = AgentConfigOutputDTO(
            provider="ollama",
            name="Test",
            model="phi:latest",
            instructions="Test",
            config=complex_config,
            history=[],
        )

        result = dto.to_dict()

        assert result["configs"] == complex_config


@pytest.mark.unit
class TestChatInputDTO:
    def test_create_with_message(self):
        dto = ChatInputDTO(message="Hello")

        assert dto.message == "Hello"

    def test_validate_success(self):
        dto = ChatInputDTO(message="Valid message")
        dto.validate()

    def test_validate_empty_message(self):
        dto = ChatInputDTO(message="")

        with pytest.raises(ValueError, match="'message'.*obrigatório"):
            dto.validate()

    def test_validate_whitespace_message(self):
        dto = ChatInputDTO(message="   ")

        with pytest.raises(ValueError, match="'message'.*obrigatório"):
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

    def test_validate_with_numeric_string_message(self):
        dto = ChatInputDTO(message="12345")
        dto.validate()

    def test_validate_empty_string_after_numeric_validation(self):
        """Testa que validação funciona corretamente com strings vazias."""
        dto = ChatInputDTO(message="")

        with pytest.raises(ValueError, match="'message'.*obrigatório"):
            dto.validate()


@pytest.mark.unit
class TestChatOutputDTO:
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

    def test_to_dict_with_special_characters(self):
        special = "Response with special chars: 你好 🎉 @#$%"
        dto = ChatOutputDTO(response=special)

        result = dto.to_dict()

        assert result["response"] == special

    def test_to_dict_has_only_response_key(self):
        dto = ChatOutputDTO(response="Test")

        result = dto.to_dict()

        assert len(result) == 1
        assert "response" in result


@pytest.mark.unit
class TestDTOsIntegration:
    def test_create_agent_to_config_flow(self):
        # Input DTO
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test instructions",
            config={"temperature": 0.8},
        )
        input_dto.validate()

        # Simula criação de agente e config output
        output_dto = AgentConfigOutputDTO(
            provider=input_dto.provider,
            name=input_dto.name,
            model=input_dto.model,
            instructions=input_dto.instructions,
            config=input_dto.config,
            history=[],
        )

        assert output_dto.name == input_dto.name
        assert output_dto.model == input_dto.model
        assert output_dto.provider == input_dto.provider
        assert output_dto.config == input_dto.config

    def test_chat_input_to_output_flow(self):
        input_dto = ChatInputDTO(message="Hello")
        input_dto.validate()

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

    def test_multiple_validations_same_dto(self):
        """Testa que validar múltiplas vezes o mesmo DTO não causa problemas."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        dto.validate()
        dto.validate()
        dto.validate()

    def test_chat_input_output_with_special_content(self):
        special_message = "こんにちは! How are you? 🤖"
        input_dto = ChatInputDTO(message=special_message)
        input_dto.validate()

        output_dto = ChatOutputDTO(response=f"Echo: {special_message}")
        output_result = output_dto.to_dict()

        assert input_dto.message == special_message
        assert special_message in output_result["response"]

    def test_config_preservation_through_dtos(self):
        """Testa que config é preservada corretamente através dos DTOs."""
        original_config = {
            "temperature": 0.8,
            "max_tokens": 2048,
            "top_p": 0.95,
            "presence_penalty": 0.1,
        }

        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-4",
            name="Advanced Agent",
            instructions="Detailed instructions",
            config=original_config,
        )
        input_dto.validate()

        output_dto = AgentConfigOutputDTO(
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=input_dto.instructions,
            config=input_dto.config,
            history=[],
        )

        result = output_dto.to_dict()

        assert result["configs"] == original_config
