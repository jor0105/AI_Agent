from typing import Any
from unittest.mock import patch

import pytest

from createagents.application import ChatRepository, ChatWithAgentUseCase
from createagents.domain import BaseTool, ChatMetrics
from createagents.main import CreateAgent
from tests.test_constants import OPENAI_MODEL_MINI


class RecordingChatRepository(ChatRepository):
    """Deterministic repository that exposes histories passed by the use case."""

    def __init__(self) -> None:
        self.histories: list[list[dict[str, str]]] = []

    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str:
        self.histories.append(history)
        return f'Response {len(self.histories)} to: {user_ask}'

    def get_metrics(self) -> list[ChatMetrics]:
        return []


@pytest.mark.unit
class TestCreateAgentHistoryWorkflow:
    @patch(
        'createagents.main.facade.client.AgentComposer.create_chat_use_case'
    )
    @pytest.mark.asyncio
    async def test_chat_clear_history_then_chat_starts_clean_conversation(
        self, mock_create_chat
    ):
        repository = RecordingChatRepository()
        mock_create_chat.return_value = ChatWithAgentUseCase(repository)
        agent = CreateAgent(
            provider='openai',
            model=OPENAI_MODEL_MINI,
            name='History workflow',
            instructions='Respond deterministically.',
        )

        first_response = await agent.chat('First message')
        second_response = await agent.chat('Second message')

        assert first_response == 'Response 1 to: First message'
        assert second_response == 'Response 2 to: Second message'
        assert repository.histories == [
            [],
            [
                {'role': 'user', 'content': 'First message'},
                {
                    'role': 'assistant',
                    'content': 'Response 1 to: First message',
                },
            ],
        ]
        assert agent.get_configs()['history'] == [
            {'role': 'user', 'content': 'First message'},
            {'role': 'assistant', 'content': 'Response 1 to: First message'},
            {'role': 'user', 'content': 'Second message'},
            {'role': 'assistant', 'content': 'Response 2 to: Second message'},
        ]

        agent.clear_history()

        configs_after_clear = agent.get_configs()
        assert configs_after_clear['history'] == []
        assert configs_after_clear['model'] == OPENAI_MODEL_MINI
        assert configs_after_clear['name'] == 'History workflow'
        assert (
            configs_after_clear['instructions'] == 'Respond deterministically.'
        )

        third_response = await agent.chat('Third message')

        assert third_response == 'Response 3 to: Third message'
        assert repository.histories[-1] == []
        assert agent.get_configs()['history'] == [
            {'role': 'user', 'content': 'Third message'},
            {'role': 'assistant', 'content': 'Response 3 to: Third message'},
        ]
