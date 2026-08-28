from unittest.mock import AsyncMock, patch

import pytest

from createagents.application import ChatInputDTO, ChatRepository
from createagents.domain import Agent
from createagents.main import AgentComposer


@pytest.mark.unit
class TestAgentComposerContracts:
    @pytest.mark.asyncio
    async def test_create_chat_use_case_proves_repository_injection(self):
        fake_repo = AsyncMock(spec=ChatRepository)
        fake_repo.chat.return_value = 'Injected response'
        fake_repo.get_metrics.return_value = []

        with patch(
            'createagents.main.composers.agent_composer.ChatAdapterFactory.create',
            return_value=fake_repo,
        ) as mock_factory_create:
            use_case = AgentComposer.create_chat_use_case(provider='openai')
            mock_factory_create.assert_called_once_with('openai')

            agent = Agent(
                provider='openai',
                model='gpt-5-mini',
                name='InjectedAgent',
                instructions='Test instructions',
                config={'temperature': 0.7},
            )
            input_dto = ChatInputDTO(message='Hello from user')

            output_dto = await use_case.execute(agent, input_dto)

            assert output_dto.response == 'Injected response'
            fake_repo.chat.assert_awaited_once_with(
                model='gpt-5-mini',
                instructions='Test instructions',
                config={'temperature': 0.7},
                tools=None,
                history=[],
                user_ask='Hello from user',
            )
