from types import SimpleNamespace
from typing import Any, ClassVar, cast

import pytest

from createagents.domain import BaseTool, ChatException, ChatMetrics
from createagents.infra.adapters.ollama.ollama_client import (
    OllamaClient,
    OllamaMessage,
)
from createagents.infra.adapters.ollama.ollama_handler import OllamaHandler
from createagents.infra.config import EnvironmentConfig


class FakeMessage:
    """Controlled model message used by the handler state-machine tests."""

    def __init__(self, content: str | None, tool_calls: object = None) -> None:
        self.content = content
        self.tool_calls = tool_calls


class FakeResponse(dict[str, int]):
    """Response shape used by the Ollama client boundary."""

    def __init__(
        self,
        content: str | None,
        tool_calls: object = None,
        metrics: dict[str, int] | None = None,
    ) -> None:
        super().__init__(metrics or {})
        self.message = FakeMessage(content, tool_calls)


class FakeOllamaClient:
    """Records each provider request and returns predetermined responses."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = iter(responses)
        self.calls: list[dict[str, Any]] = []

    async def call_api(
        self,
        model: str,
        messages: list[Any],
        config: dict[str, Any] | None,
        tools: list[dict[str, Any]] | None,
    ) -> FakeResponse:
        self.calls.append(
            {
                'model': model,
                'messages': list(messages),
                'config': config,
                'tools': tools,
            }
        )
        return next(self._responses)


class DummyTool(BaseTool):
    """Deterministic tool used to drive the actual tool executor."""

    name = 'dummy'
    description = 'Returns its argument'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {
            'value': {'type': 'string', 'description': 'Value to return'}
        },
        'required': ['value'],
    }

    def execute(self, value: str) -> str:
        return f'tool result: {value}'


def _create_handler(
    responses: list[FakeResponse],
    metrics: list[ChatMetrics] | None = None,
) -> tuple[OllamaHandler, FakeOllamaClient]:
    """Build a handler around a client fake without replacing its logic."""
    client = FakeOllamaClient(responses)
    handler = OllamaHandler(cast(OllamaClient, client), metrics)
    return handler, client


@pytest.mark.unit
class TestOllamaHandler:
    @pytest.mark.asyncio
    async def test_empty_response_retries_without_mutating_messages(self):
        original_messages: list[OllamaMessage] = [
            {'role': 'user', 'content': 'What did we learn?'}
        ]
        metrics: list[ChatMetrics] = []
        handler, client = _create_handler(
            [
                FakeResponse(content=''),
                FakeResponse(
                    content='A final response.',
                    metrics={'prompt_eval_count': 2, 'eval_count': 3},
                ),
            ],
            metrics,
        )

        result = await handler.execute_tool_loop(
            model='test-model',
            messages=original_messages,
            config={'temperature': 0.2},
            tools=None,
        )

        retry_messages = client.calls[1]['messages']
        assert result == 'A final response.'
        assert original_messages == [
            {'role': 'user', 'content': 'What did we learn?'}
        ]
        assert retry_messages[:-1] == original_messages
        assert retry_messages[-1] == {
            'role': 'user',
            'content': (
                'Based on the information gathered, please provide a final '
                'answer to the original question.'
            ),
        }
        assert client.calls[1]['tools'] is None
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 5

    @pytest.mark.asyncio
    async def test_two_empty_responses_summarize_three_tool_results(self):
        long_result = 'a' * 600
        messages: list[OllamaMessage] = [
            {
                'role': 'tool',
                'tool_name': f'tool-{index}',
                'content': long_result if index == 0 else f'result {index}',
            }
            for index in range(4)
        ]
        handler, client = _create_handler(
            [
                FakeResponse(content=''),
                FakeResponse(content=''),
                FakeResponse(content=''),
            ]
        )

        result = await handler.execute_tool_loop(
            model='test-model',
            messages=messages,
            config=None,
            tools=None,
        )

        assert result.startswith('Based on the gathered information:\n\n')
        assert f'From tool-0: {long_result[:500]}' in result
        assert long_result[:501] not in result
        assert 'From tool-1: result 1' in result
        assert 'From tool-2: result 2' in result
        assert 'tool-3' not in result
        assert len(client.calls) == 3
        assert client.calls[1]['tools'] is None

    @pytest.mark.asyncio
    async def test_two_empty_responses_without_tool_results_raise_error(self):
        metrics: list[ChatMetrics] = []
        handler, _ = _create_handler(
            [
                FakeResponse(content=''),
                FakeResponse(content=''),
                FakeResponse(content=''),
            ],
            metrics,
        )

        with pytest.raises(
            ChatException, match='Ollama returned multiple empty responses'
        ):
            await handler.execute_tool_loop(
                model='test-model',
                messages=[],
                config=None,
                tools=None,
            )

        assert len(metrics) == 1
        assert metrics[0].success is False

    @pytest.mark.asyncio
    async def test_tool_call_without_tools_records_an_error_metric(self):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(name='dummy', arguments={'value': 'one'})
        )
        metrics: list[ChatMetrics] = []
        handler, _ = _create_handler(
            [FakeResponse(content='', tool_calls=[tool_call])],
            metrics,
        )

        with pytest.raises(
            ChatException,
            match='Tool calls detected but no tools were provided',
        ):
            await handler.execute_tool_loop(
                model='test-model',
                messages=[],
                config=None,
                tools=None,
            )

        assert len(metrics) == 1
        assert metrics[0].success is False

    @pytest.mark.asyncio
    async def test_tool_call_uses_real_executor_and_returns_final_response(
        self,
    ):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name='dummy',
                arguments={'value': 'one'},
            )
        )
        metrics: list[ChatMetrics] = []
        handler, client = _create_handler(
            [
                FakeResponse(content='', tool_calls=[tool_call]),
                FakeResponse(
                    content='Tool output was used.',
                    metrics={'prompt_eval_count': 1, 'eval_count': 1},
                ),
            ],
            metrics,
        )

        result = await handler.execute_tool_loop(
            model='test-model',
            messages=[{'role': 'user', 'content': 'Run the tool.'}],
            config=None,
            tools=[DummyTool()],
        )

        tool_messages = [
            message
            for message in client.calls[1]['messages']
            if isinstance(message, dict) and message.get('role') == 'tool'
        ]
        assert result == 'Tool output was used.'
        assert tool_messages == [
            {
                'role': 'tool',
                'tool_name': 'dummy',
                'content': 'tool result: one',
            }
        ]
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 2

    @pytest.mark.asyncio
    async def test_tool_loop_raises_when_iteration_limit_is_exhausted(
        self, monkeypatch
    ):
        monkeypatch.setenv('OLLAMA_MAX_TOOL_ITERATIONS', '1')
        EnvironmentConfig.clear_cache()
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name='dummy',
                arguments={'value': 'one'},
            )
        )
        metrics: list[ChatMetrics] = []
        handler, client = _create_handler(
            [FakeResponse(content='', tool_calls=[tool_call])],
            metrics,
        )

        try:
            with pytest.raises(
                ChatException,
                match=r'Max tool calling iterations \(1\) exceeded',
            ):
                await handler.execute_tool_loop(
                    model='test-model',
                    messages=[],
                    config=None,
                    tools=[DummyTool()],
                )
        finally:
            EnvironmentConfig.clear_cache()

        assert len(client.calls) == 1
        assert client.calls[0]['tools'] is not None
        assert len(metrics) == 1
        assert metrics[0].success is False
