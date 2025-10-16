import pytest

from src.application.dtos import ChatInputDTO
from src.application.use_cases.chat_with_agent import ChatWithAgentUseCase
from src.domain.entities.agent_domain import Agent
from src.domain.exceptions import ChatException


@pytest.mark.unit
class TestChatWithAgentUseCase:
    def test_execute_with_valid_input(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = "AI response"
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Be helpful",
        )
        input_dto = ChatInputDTO(message="Hello")

        output = use_case.execute(agent, input_dto)

        assert output.response == "AI response"

    def test_execute_adds_messages_to_history(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = "Response"
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="User message")

        use_case.execute(agent, input_dto)

        assert len(agent.history) == 2
        messages = agent.history.get_messages()
        assert messages[0].content == "User message"
        assert messages[1].content == "Response"

    def test_execute_calls_repository_with_correct_params(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = "Response"
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="ollama",
            model="phi4-mini:latest",
            name="Test",
            instructions="Instructions",
        )
        input_dto = ChatInputDTO(message="Test message")

        use_case.execute(agent, input_dto)

        mock_chat_repository.chat.assert_called_once_with(
            model="phi4-mini:latest",
            instructions="Instructions",
            config={},
            user_ask="Test message",
            history=[],
        )

    def test_execute_with_existing_history(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = "Response"
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        agent.add_user_message("Previous message")
        agent.add_assistant_message("Previous response")
        input_dto = ChatInputDTO(message="New message")

        use_case.execute(agent, input_dto)

        call_args = mock_chat_repository.chat.call_args
        assert len(call_args.kwargs["history"]) == 2

    def test_execute_with_empty_message_raises_error(self, mock_chat_repository):
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="")

        with pytest.raises(ValueError):
            use_case.execute(agent, input_dto)

    def test_execute_propagates_chat_exception(self, mock_chat_repository):
        mock_chat_repository.chat.side_effect = ChatException("API error")
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="API error"):
            use_case.execute(agent, input_dto)

    def test_execute_wraps_value_error(self, mock_chat_repository):
        mock_chat_repository.chat.side_effect = ValueError("Invalid value")
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="Erro de validação"):
            use_case.execute(agent, input_dto)

    def test_execute_wraps_type_error(self, mock_chat_repository):
        mock_chat_repository.chat.side_effect = TypeError("Invalid type")
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="Erro de tipo"):
            use_case.execute(agent, input_dto)

    def test_execute_wraps_key_error(self, mock_chat_repository):
        mock_chat_repository.chat.side_effect = KeyError("missing_key")
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="Erro ao processar resposta"):
            use_case.execute(agent, input_dto)

    def test_execute_wraps_generic_exception(self, mock_chat_repository):
        mock_chat_repository.chat.side_effect = RuntimeError("Unexpected error")
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="Erro inesperado"):
            use_case.execute(agent, input_dto)

    def test_execute_does_not_add_to_history_on_error(self, mock_chat_repository):
        mock_chat_repository.chat.side_effect = ChatException("Error")
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException):
            use_case.execute(agent, input_dto)

        assert len(agent.history) == 0

    def test_execute_with_empty_response_raises_error(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = ""
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="Resposta vazia"):
            use_case.execute(agent, input_dto)

        assert len(agent.history) == 0

    def test_execute_with_none_response_raises_error(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = None
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="Test")

        with pytest.raises(ChatException, match="Resposta vazia"):
            use_case.execute(agent, input_dto)

        assert len(agent.history) == 0

    def test_execute_with_agent_config(self, mock_chat_repository):
        mock_chat_repository.chat.return_value = "Response"
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        config = {"temperature": 0.7, "max_tokens": 100}
        agent = Agent(
            provider="openai",
            model="gpt-4",
            name="Test",
            instructions="Test",
            config=config,
        )
        input_dto = ChatInputDTO(message="Test message")

        use_case.execute(agent, input_dto)

        mock_chat_repository.chat.assert_called_once_with(
            model="gpt-4",
            instructions="Test",
            config=config,
            user_ask="Test message",
            history=[],
        )

    def test_get_metrics_when_repository_supports_it(self):
        from unittest.mock import Mock

        # Cria um mock sem spec para permitir get_metrics
        mock_repository = Mock()
        mock_repository.get_metrics.return_value = [
            {"timestamp": "2024-01-01", "model": "gpt-4"}
        ]
        use_case = ChatWithAgentUseCase(chat_repository=mock_repository)

        metrics = use_case.get_metrics()

        assert len(metrics) == 1
        assert metrics[0]["model"] == "gpt-4"
        mock_repository.get_metrics.assert_called_once()

    def test_get_metrics_when_repository_does_not_support_it(
        self, mock_chat_repository
    ):
        # O mock com spec não permite chamar get_metrics que não está na interface
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)

        metrics = use_case.get_metrics()

        # Deve retornar lista vazia se o repositório não tem get_metrics
        assert metrics == []

    def test_execute_validates_input_dto(self, mock_chat_repository):
        use_case = ChatWithAgentUseCase(chat_repository=mock_chat_repository)
        agent = Agent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )
        input_dto = ChatInputDTO(message="   ")

        with pytest.raises(ValueError, match="message"):
            use_case.execute(agent, input_dto)

        mock_chat_repository.chat.assert_not_called()
