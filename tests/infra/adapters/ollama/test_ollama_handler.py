from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from createagents.domain import BaseTool
from createagents.infra.adapters.ollama.ollama_handler import OllamaHandler


class FakeMessage:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeResponse(dict):
    def __init__(self, content, tool_calls=None, metrics=None):
        super().__init__(metrics or {})
        self.message = FakeMessage(content, tool_calls)


class DummyTool(BaseTool):
    name = 'dummy'
    description = 'dummy tool'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {},
    }

    def execute(self, **kwargs):
        return kwargs


@pytest.mark.unit
class TestOllamaHandler:
    @pytest.mark.asyncio
    async def test_execute_tool_loop_scenarios_returns_final_response(self):
        metrics_store = []
        client = MagicMock()
        client.call_api = AsyncMock(
            return_value=FakeResponse(
                content='final response',
                metrics={'prompt_eval_count': 2, 'eval_count': 3},
            )
        )

        handler = OllamaHandler(client, metrics_store)

        result = await handler.execute_tool_loop(
            model='test-model',
            messages=[],
            config=None,
            tools=None,
        )

        assert result == 'final response'
        assert len(metrics_store) == 1
        assert metrics_store[0].success is True
        assert metrics_store[0].tokens_used == 5

    @pytest.mark.asyncio
    @patch('createagents.infra.adapters.common.tool_session.ToolExecutor')
    async def test_execute_tool_loop_scenarios_executes_tool_calls(
        self, mock_tool_executor
    ):
        metrics_store = []
        client = MagicMock()
        tool_call = SimpleNamespace(
            function=SimpleNamespace(name='dummy', arguments={'value': 1})
        )
        response_with_tool = FakeResponse(content='', tool_calls=[tool_call])
        final_response = FakeResponse(
            content='done', metrics={'prompt_eval_count': 1, 'eval_count': 1}
        )
        client.call_api = AsyncMock(
            side_effect=[response_with_tool, final_response]
        )

        executor_instance = SimpleNamespace(
            execute_tool=AsyncMock(
                return_value=SimpleNamespace(success=True, result='ok')
            )
        )
        mock_tool_executor.return_value = executor_instance

        handler = OllamaHandler(client, metrics_store)

        result = await handler.execute_tool_loop(
            model='test-model',
            messages=[{'role': 'user', 'content': 'Hi'}],
            config=None,
            tools=[DummyTool()],
        )

        assert result == 'done'
        executor_instance.execute_tool.assert_awaited_once_with(
            'dummy', value=1
        )
        assert len(metrics_store) == 1
        assert metrics_store[0].tokens_used == 2
