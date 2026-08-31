from collections.abc import AsyncGenerator
from typing import Any, TypedDict

import pytest

from createagents.application.interfaces.chat_repository import (
    ChatRepository,
)
from createagents.domain import ChatMetrics
from createagents.domain.value_objects.base_tools import BaseTool
from tests.test_constants import OPENAI_MODEL_MINI


class TestToolForRepo(BaseTool):
    name = 'test'
    description = 'test'

    def execute(self, *args: object, **kwargs: object) -> int:
        return 1


class RepositoryCall(TypedDict):
    """Arguments captured by the parameter-checking repository."""

    model: str
    instructions: str
    config: dict[str, Any]
    tools: list[BaseTool]
    history: list[dict[str, str]]
    user_ask: str


@pytest.mark.unit
class TestChatRepository:
    def test_scenario_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            from tests.typing_helpers import invoke

            invoke(ChatRepository)

    def test_scenario_concrete_implementation_must_implement_chat(self):
        class IncompleteRepository(ChatRepository):
            __slots__ = ()

        with pytest.raises(TypeError):
            from tests.typing_helpers import invoke

            invoke(IncompleteRepository)

    @pytest.mark.asyncio
    async def test_scenario_concrete_implementation_with_chat_method(self):
        class ConcreteRepository(ChatRepository):
            async def chat(
                self,
                model: str,
                instructions: str | None,
                config: dict[str, Any] | None,
                tools: list[BaseTool] | None,
                history: list[dict[str, str]],
                user_ask: str,
            ) -> str:
                return f'Response to: {user_ask}'

            def get_metrics(self) -> list[ChatMetrics]:
                return []

        repo = ConcreteRepository()
        assert isinstance(repo, ChatRepository)

        result = await repo.chat(
            model=OPENAI_MODEL_MINI,
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
                self,
                model: str,
                instructions: str | None,
                config: dict[str, Any] | None,
                tools: list[BaseTool] | None,
                history: list[dict[str, str]],
                user_ask: str,
            ) -> str:
                return 'Complete response'

            def get_metrics(self) -> list[ChatMetrics]:
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
                self,
                model: str,
                instructions: str | None,
                config: dict[str, Any] | None,
                tools: list[BaseTool] | None,
                history: list[dict[str, str]],
                user_ask: str,
            ) -> AsyncGenerator[str, None]:
                async def generator() -> AsyncGenerator[str, None]:
                    yield 'token1'
                    yield 'token2'
                    yield 'token3'

                return generator()

            def get_metrics(self) -> list[ChatMetrics]:
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
            def __init__(self) -> None:
                self.last_call: RepositoryCall | None = None

            async def chat(
                self,
                model: str,
                instructions: str | None,
                config: dict[str, Any] | None,
                tools: list[BaseTool] | None,
                history: list[dict[str, str]],
                user_ask: str,
            ) -> str:
                if instructions is None or config is None:
                    raise AssertionError('required test values were omitted')
                if tools is None:
                    raise AssertionError('required test tools were omitted')
                self.last_call = {
                    'model': model,
                    'instructions': instructions,
                    'config': config,
                    'tools': tools,
                    'history': history,
                    'user_ask': user_ask,
                }
                return 'ok'

            def get_metrics(self) -> list[ChatMetrics]:
                return []

        repo = ParameterCheckRepository()
        tool = TestToolForRepo()

        await repo.chat(
            model=OPENAI_MODEL_MINI,
            instructions='You are helpful',
            config={'temperature': 0.7},
            tools=[tool],
            history=[{'role': 'user', 'content': 'Hi'}],
            user_ask='Hello',
        )

        assert repo.last_call is not None
        assert repo.last_call['model'] == OPENAI_MODEL_MINI
        assert repo.last_call['instructions'] == 'You are helpful'
        assert repo.last_call['config'] == {'temperature': 0.7}
        assert len(repo.last_call['tools']) == 1
        assert repo.last_call['history'] == [{'role': 'user', 'content': 'Hi'}]
        assert repo.last_call['user_ask'] == 'Hello'
