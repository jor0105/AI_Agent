from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest

from createagents.application import (
    ChatInputDTO,
    ChatOutputDTO,
    ChatWithAgentUseCase,
)
from createagents.domain import Agent, ChatException, ChatMetrics


@pytest.fixture
def mock_async_chat_repository():
    """Fixture that creates an async mock chat repository."""
    mock = Mock()
    mock.chat = AsyncMock(return_value='AI response')
    mock.get_metrics.return_value = []
    return mock


@pytest.mark.unit
class TestChatWithAgentUseCase:
    @pytest.mark.asyncio
    async def test_execute_with_valid_input(self, mock_async_chat_repository):
        mock_async_chat_repository.chat.return_value = 'AI response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Be helpful',
        )
        input_dto = ChatInputDTO(message='Hello')

        output = await use_case.execute(agent, input_dto)

        assert isinstance(output, ChatOutputDTO)
        assert output.response == 'AI response'

    @pytest.mark.asyncio
    async def test_execute_adds_messages_to_history(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='User message')

        await use_case.execute(agent, input_dto)

        assert len(agent.history) == 2
        messages = agent.history.get_messages()
        assert messages[0].content == 'User message'
        assert messages[1].content == 'Response'

    @pytest.mark.asyncio
    async def test_execute_calls_repository_with_correct_params(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='ollama',
            model='phi4-mini:latest',
            name='Test',
            instructions='Instructions',
        )
        input_dto = ChatInputDTO(message='Test message')

        await use_case.execute(agent, input_dto)

        mock_async_chat_repository.chat.assert_called_once_with(
            model='phi4-mini:latest',
            instructions='Instructions',
            config=None,
            user_ask='Test message',
            history=[],
            tools=None,
        )

    @pytest.mark.asyncio
    async def test_execute_with_existing_history(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        agent.add_user_message('Previous message')
        agent.add_assistant_message('Previous response')
        input_dto = ChatInputDTO(message='New message')

        await use_case.execute(agent, input_dto)

        call_args = mock_async_chat_repository.chat.call_args
        assert len(call_args.kwargs['history']) == 2

    @pytest.mark.asyncio
    async def test_execute_with_empty_message_raises_error(
        self, mock_async_chat_repository
    ):
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='')

        with pytest.raises(ValueError):
            await use_case.execute(agent, input_dto)

    @pytest.mark.asyncio
    async def test_execute_propagates_chat_exception(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.side_effect = ChatException(
            'API error'
        )
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException, match='API error'):
            await use_case.execute(agent, input_dto)

    @pytest.mark.asyncio
    async def test_execute_wraps_value_error(self, mock_async_chat_repository):
        mock_async_chat_repository.chat.side_effect = ValueError(
            'Invalid value'
        )
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException, match='Validation error'):
            await use_case.execute(agent, input_dto)

    @pytest.mark.asyncio
    async def test_execute_wraps_type_error(self, mock_async_chat_repository):
        mock_async_chat_repository.chat.side_effect = TypeError('Invalid type')
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException, match='Type error'):
            await use_case.execute(agent, input_dto)

    @pytest.mark.asyncio
    async def test_execute_wraps_key_error(self, mock_async_chat_repository):
        mock_async_chat_repository.chat.side_effect = KeyError('missing_key')
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(
            ChatException, match='Error processing AI response'
        ):
            await use_case.execute(agent, input_dto)

    @pytest.mark.asyncio
    async def test_execute_wraps_generic_exception(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.side_effect = RuntimeError(
            'Unexpected error'
        )
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException, match='Unexpected error'):
            await use_case.execute(agent, input_dto)

    @pytest.mark.asyncio
    async def test_execute_does_not_add_to_history_on_error(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.side_effect = ChatException('Error')
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException):
            await use_case.execute(agent, input_dto)

        assert len(agent.history) == 0

    @pytest.mark.asyncio
    async def test_execute_with_empty_response_raises_error(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = ''
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException, match='Empty response'):
            await use_case.execute(agent, input_dto)

        assert len(agent.history) == 0

    @pytest.mark.asyncio
    async def test_execute_with_none_response_raises_error(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = None
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='Test')

        with pytest.raises(ChatException, match='Empty response'):
            await use_case.execute(agent, input_dto)

        assert len(agent.history) == 0

    @pytest.mark.asyncio
    async def test_execute_with_agent_config(self, mock_async_chat_repository):
        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        config = {'temperature': 0.7, 'max_tokens': 100}
        agent = Agent(
            provider='openai',
            model='gpt-4',
            name='Test',
            instructions='Test',
            config=config,
        )
        input_dto = ChatInputDTO(message='Test message')

        await use_case.execute(agent, input_dto)

        mock_async_chat_repository.chat.assert_called_once_with(
            model='gpt-4',
            instructions='Test',
            config=config,
            user_ask='Test message',
            history=[],
            tools=None,
        )

    def test_get_metrics_when_repository_supports_it(self):
        mock_repository = Mock()
        mock_repository.get_metrics.return_value = [
            ChatMetrics(model='gpt-4', latency_ms=1.0)
        ]
        use_case = ChatWithAgentUseCase(chat_repository=mock_repository)

        metrics = use_case.get_metrics()

        assert len(metrics) == 1
        assert metrics[0].model == 'gpt-4'
        mock_repository.get_metrics.assert_called_once()

    def test_get_metrics_returns_empty_list_when_no_metrics(
        self, mock_async_chat_repository
    ):
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )

        metrics = use_case.get_metrics()

        assert metrics == []

    @pytest.mark.asyncio
    async def test_execute_validates_input_dto(
        self, mock_async_chat_repository
    ):
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        input_dto = ChatInputDTO(message='   ')

        with pytest.raises(ValueError, match='message'):
            await use_case.execute(agent, input_dto)

        mock_async_chat_repository.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_long_message(self, mock_async_chat_repository):
        mock_async_chat_repository.chat.return_value = (
            'Response to long message'
        )
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        long_message = 'A' * 10000
        input_dto = ChatInputDTO(message=long_message)

        output = await use_case.execute(agent, input_dto)

        assert isinstance(output, ChatOutputDTO)
        assert output.response == 'Response to long message'
        assert len(agent.history) == 2

    @pytest.mark.asyncio
    async def test_execute_preserves_message_order(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )

        input_dto1 = ChatInputDTO(message='First message')
        await use_case.execute(agent, input_dto1)

        input_dto2 = ChatInputDTO(message='Second message')
        await use_case.execute(agent, input_dto2)

        messages = agent.history.get_messages()
        assert len(messages) == 4
        assert messages[0].content == 'First message'
        assert messages[1].content == 'Response'
        assert messages[2].content == 'Second message'
        assert messages[3].content == 'Response'

    @pytest.mark.asyncio
    async def test_execute_with_special_characters_in_message(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
        )
        special_message = 'Hello! 你好 🤖 @#$%'
        input_dto = ChatInputDTO(message=special_message)

        output = await use_case.execute(agent, input_dto)

        assert isinstance(output, ChatOutputDTO)
        assert output.response == 'Response'
        messages = agent.history.get_messages()
        assert messages[0].content == special_message

    @pytest.mark.asyncio
    async def test_execute_respects_history_max_size(
        self, mock_async_chat_repository
    ):
        from createagents.domain.entities import History

        mock_async_chat_repository.chat.return_value = 'Response'
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = Agent(
            provider='openai',
            model='gpt-5-nano',
            name='Test',
            instructions='Test',
            history=History(max_size=4),
        )

        for i in range(3):
            input_dto = ChatInputDTO(message=f'Message {i}')
            await use_case.execute(agent, input_dto)

        assert len(agent.history) == 4
        messages = agent.history.get_messages()
        assert messages[0].content == 'Message 1'


def _agent() -> Agent:
    return Agent(
        provider='openai',
        model='gpt-5-nano',
        name='Test',
        instructions='Be helpful',
    )


async def _stream(*tokens: str) -> AsyncGenerator[str, None]:
    for token in tokens:
        yield token


@pytest.mark.unit
class TestChatWithAgentStreaming:
    """The streaming branch: tokens pass through, history lands at the end."""

    @pytest.mark.asyncio
    async def test_yields_every_token_in_order(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = _stream(
            'Hello', ', ', 'world'
        )
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )

        result = await use_case.execute(_agent(), ChatInputDTO(message='Hi'))

        assert isinstance(result, AsyncGenerator)
        assert [token async for token in result] == ['Hello', ', ', 'world']

    @pytest.mark.asyncio
    async def test_history_is_updated_only_after_the_stream_ends(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = _stream('a', 'b')
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = _agent()

        result = await use_case.execute(agent, ChatInputDTO(message='Hi'))

        collected: list[str] = []
        assert isinstance(result, AsyncGenerator)
        async for token in result:
            collected.append(token)
            # Mid-stream the history must still be untouched.
            assert len(agent.history) == 0

        assert collected == ['a', 'b']
        messages = agent.history.get_messages()
        assert len(messages) == 2
        assert messages[0].content == 'Hi'
        assert messages[1].content == 'ab'

    @pytest.mark.asyncio
    async def test_empty_stream_raises_chat_exception(
        self, mock_async_chat_repository
    ):
        mock_async_chat_repository.chat.return_value = _stream()
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = _agent()

        result = await use_case.execute(agent, ChatInputDTO(message='Hi'))

        assert isinstance(result, AsyncGenerator)
        with pytest.raises(
            ChatException, match='Empty response received from stream'
        ):
            [token async for token in result]

        assert len(agent.history) == 0

    @pytest.mark.asyncio
    async def test_error_mid_stream_is_wrapped_in_chat_exception(
        self, mock_async_chat_repository
    ):
        async def failing_stream() -> AsyncGenerator[str, None]:
            yield 'partial'
            raise RuntimeError('connection dropped')

        mock_async_chat_repository.chat.return_value = failing_stream()
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )
        agent = _agent()

        result = await use_case.execute(agent, ChatInputDTO(message='Hi'))

        assert isinstance(result, AsyncGenerator)
        with pytest.raises(ChatException) as exc_info:
            [token async for token in result]

        assert 'connection dropped' in str(exc_info.value)
        assert isinstance(exc_info.value.original_error, RuntimeError)
        assert len(agent.history) == 0

    @pytest.mark.asyncio
    async def test_chat_exception_mid_stream_propagates_unwrapped(
        self, mock_async_chat_repository
    ):
        async def failing_stream() -> AsyncGenerator[str, None]:
            yield 'partial'
            raise ChatException('provider refused')

        mock_async_chat_repository.chat.return_value = failing_stream()
        use_case = ChatWithAgentUseCase(
            chat_repository=mock_async_chat_repository
        )

        result = await use_case.execute(_agent(), ChatInputDTO(message='Hi'))

        assert isinstance(result, AsyncGenerator)
        with pytest.raises(
            ChatException, match='provider refused'
        ) as exc_info:
            [token async for token in result]

        assert exc_info.value.original_error is None
