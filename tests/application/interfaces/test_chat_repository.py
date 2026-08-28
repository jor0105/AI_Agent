import pytest

from createagents.application.interfaces.chat_repository import (
    ChatRepository,
)
from createagents.domain.value_objects.base_tools import BaseTool


class TestToolForRepo(BaseTool):
    name = 'test'
    description = 'test'

    def execute(self, *args, **kwargs):
        return 1


@pytest.mark.unit
class TestChatRepository:
    def test_scenario_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            ChatRepository()

    def test_scenario_concrete_implementation_must_implement_chat(self):
        class IncompleteRepository(ChatRepository):
            __slots__ = ()

        with pytest.raises(TypeError):
            IncompleteRepository()

    @pytest.mark.asyncio
    async def test_scenario_concrete_implementation_with_chat_method(self):
        class ConcreteRepository(ChatRepository):
            async def chat(
                self, model, instructions, config, tools, history, user_ask
            ):
                return f'Response to: {user_ask}'

            def get_metrics(self):
                return []

        repo = ConcreteRepository()
        assert isinstance(repo, ChatRepository)

        result = await repo.chat(
            model='gpt-4',
            instructions='Test',
            config={},
            tools=None,
            history=[],
            user_ask='Hello',
        )
        assert result == 'Response to: Hello'

    @pytest.mark.asyncio
    async def test_scenario_chat_method_returns_string(self):
        class StringRepository(ChatRepository):
            async def chat(
                self, model, instructions, config, tools, history, user_ask
            ):
                return 'Complete response'

            def get_metrics(self):
                return []

        repo = StringRepository()
        result = await repo.chat(
            model='test-model',
            instructions=None,
            config=None,
            tools=None,
            history=[],
            user_ask='Test',
        )

        assert isinstance(result, str)
        assert result == 'Complete response'

    @pytest.mark.asyncio
    async def test_scenario_chat_method_returns_generator(self):
        class StreamingRepository(ChatRepository):
            async def chat(
                self, model, instructions, config, tools, history, user_ask
            ):
                async def generator():
                    yield 'token1'
                    yield 'token2'
                    yield 'token3'

                return generator()

            def get_metrics(self):
                return []

        repo = StreamingRepository()
        result = await repo.chat(
            model='test-model',
            instructions=None,
            config=None,
            tools=None,
            history=[],
            user_ask='Test',
        )

        tokens = [token async for token in result]

        assert tokens == ['token1', 'token2', 'token3']

    @pytest.mark.asyncio
    async def test_scenario_chat_accepts_all_parameters(self):
        class ParameterCheckRepository(ChatRepository):
            def __init__(self):
                self.last_call = None

            async def chat(
                self, model, instructions, config, tools, history, user_ask
            ):
                self.last_call = {
                    'model': model,
                    'instructions': instructions,
                    'config': config,
                    'tools': tools,
                    'history': history,
                    'user_ask': user_ask,
                }
                return 'ok'

            def get_metrics(self):
                return []

        repo = ParameterCheckRepository()
        tool = TestToolForRepo()

        await repo.chat(
            model='gpt-4',
            instructions='You are helpful',
            config={'temperature': 0.7},
            tools=[tool],
            history=[{'role': 'user', 'content': 'Hi'}],
            user_ask='Hello',
        )

        assert repo.last_call['model'] == 'gpt-4'
        assert repo.last_call['instructions'] == 'You are helpful'
        assert repo.last_call['config'] == {'temperature': 0.7}
        assert len(repo.last_call['tools']) == 1
        assert repo.last_call['history'] == [{'role': 'user', 'content': 'Hi'}]
        assert repo.last_call['user_ask'] == 'Hello'
