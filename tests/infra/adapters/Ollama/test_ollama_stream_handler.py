from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from createagents.domain import BaseTool
from createagents.infra.adapters.Ollama.ollama_stream_handler import (
    OllamaStreamHandler,
)


class FakeChunk:
    def __init__(self, content='', tool_calls=None, metrics=None):
        metrics = metrics or {}
        self.message = SimpleNamespace(content=content, tool_calls=tool_calls)
        self.prompt_eval_count = metrics.get('prompt_eval_count')
        self.eval_count = metrics.get('eval_count')
        self.load_duration = metrics.get('load_duration')
        self.prompt_eval_duration = metrics.get('prompt_eval_duration')
        self.eval_duration = metrics.get('eval_duration')


class FakeStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self._iterator = None

    def __aiter__(self):
        self._iterator = iter(self._chunks)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class DummyTool(BaseTool):
    name = 'dummy'
    description = 'dummy tool'
    parameters = {'type': 'object', 'properties': {}}

    def execute(self, **kwargs):
        return kwargs


@pytest.mark.unit
class TestOllamaStreamHandler:
    @pytest.mark.asyncio
    async def test_handle_stream_scenarios_yields_tokens_without_tools(self):
        metrics_store = []
        client = MagicMock()
        chunks = [
            FakeChunk(content='Hel'),
            FakeChunk(
                content='lo',
                metrics={
                    'prompt_eval_count': 1,
                    'eval_count': 2,
                    'load_duration': 1_000_000,
                    'prompt_eval_duration': 2_000_000,
                    'eval_duration': 3_000_000,
                },
            ),
        ]
        client.stream_api = AsyncMock(return_value=FakeStream(chunks))

        handler = OllamaStreamHandler(client, metrics_store)

        tokens = []
        async for piece in handler.handle_stream(
            model='test-model',
            messages=[{'role': 'user', 'content': 'Hi'}],
            config={'stream': True},
            tools=None,
        ):
            tokens.append(piece)

        assert ''.join(tokens) == 'Hello'
        assert len(metrics_store) == 1
        assert metrics_store[0].tokens_used == 3
        assert metrics_store[0].load_duration_ms == 1.0
        assert metrics_store[0].prompt_eval_duration_ms == 2.0
        assert metrics_store[0].eval_duration_ms == 3.0

    @pytest.mark.asyncio
    @patch('createagents.infra.adapters.Common.tool_session.ToolExecutor')
    async def test_handle_stream_scenarios_executes_tool_calls(
        self, mock_tool_executor
    ):
        metrics_store = []
        client = MagicMock()
        tool_call = SimpleNamespace(
            function=SimpleNamespace(name='dummy', arguments={'value': 1})
        )
        stream_with_tool = FakeStream(
            [FakeChunk(content='', tool_calls=[tool_call])]
        )
        stream_with_answer = FakeStream(
            [FakeChunk(content='Answer', metrics={'eval_count': 2})]
        )
        client.stream_api = AsyncMock(
            side_effect=[stream_with_tool, stream_with_answer]
        )

        executor_instance = SimpleNamespace(
            execute_tool=AsyncMock(
                return_value=SimpleNamespace(success=True, result='ok')
            )
        )
        mock_tool_executor.return_value = executor_instance

        handler = OllamaStreamHandler(client, metrics_store)

        tokens = []
        async for piece in handler.handle_stream(
            model='test-model',
            messages=[{'role': 'user', 'content': 'Hi'}],
            config={'stream': True},
            tools=[DummyTool()],
        ):
            tokens.append(piece)

        assert ''.join(tokens) == 'Answer'
        executor_instance.execute_tool.assert_awaited_once_with(
            'dummy', value=1
        )
        assert len(metrics_store) == 1
        assert metrics_store[0].completion_tokens == 2
