from types import SimpleNamespace
from typing import ClassVar, cast
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from createagents.domain import BaseTool, ChatException
from createagents.infra.adapters.openai.openai_handler import OpenAIHandler
from tests.test_constants import OPENAI_MODEL_NANO


@pytest.mark.unit
class TestOpenAIHandler:
    def setup_method(self):
        self.mock_client = Mock()
        self.mock_client.call_api = AsyncMock()
        self.handler = OpenAIHandler(self.mock_client)

    def _make_response(
        self,
        output_text: str = '',
        tool_calls: object = None,
        usage_attrs: dict[str, object] | None = None,
    ) -> MagicMock:
        mock_response = MagicMock()
        mock_response.output_text = output_text

        if tool_calls:
            mock_response.tool_calls = tool_calls

        if usage_attrs:
            mock_usage = MagicMock()
            for k, v in usage_attrs.items():
                setattr(mock_usage, k, v)
            mock_response.usage = mock_usage
        else:
            mock_response.usage = None

        return mock_response

    @patch('createagents.infra.adapters.openai.openai_handler.ToolCallParser')
    @pytest.mark.asyncio
    async def test_execute_tool_loop_success(self, mock_parser):
        mock_parser.has_tool_calls.return_value = False

        mock_response = self._make_response(
            output_text='Success response', usage_attrs={'total_tokens': 100}
        )
        self.mock_client.call_api.return_value = mock_response

        response = await self.handler.execute_tool_loop(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={},
            tools=None,
        )

        assert response == 'Success response'
        self.mock_client.call_api.assert_called_once()

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 100

    @patch('createagents.infra.adapters.openai.openai_handler.ToolCallParser')
    @pytest.mark.asyncio
    async def test_execute_tool_loop_empty_response(self, mock_parser):
        mock_parser.has_tool_calls.return_value = False

        mock_response = self._make_response(output_text='')
        self.mock_client.call_api.return_value = mock_response

        with pytest.raises(
            ChatException, match='OpenAI returned an empty response'
        ):
            await self.handler.execute_tool_loop(
                model=OPENAI_MODEL_NANO,
                instructions='Instr',
                messages=[],
                config={},
                tools=None,
            )

    @patch('createagents.infra.adapters.openai.openai_handler.ToolCallParser')
    @pytest.mark.asyncio
    async def test_execute_tool_loop_api_error(self, mock_parser):
        self.mock_client.call_api.side_effect = RuntimeError('API Error')

        with pytest.raises(
            ChatException, match='Error communicating with OpenAI'
        ):
            await self.handler.execute_tool_loop(
                model=OPENAI_MODEL_NANO,
                instructions='Instr',
                messages=[],
                config={},
                tools=None,
            )

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert 'API Error' in metrics[0].error_message

    @patch(
        'createagents.infra.adapters.openai.openai_tool_invoker.ToolCallParser'
    )
    @patch('createagents.infra.adapters.openai.openai_handler.ToolCallParser')
    @patch('createagents.infra.adapters.common.tool_session.ToolExecutor')
    @patch(
        'createagents.infra.adapters.openai.openai_handler.ToolSchemaFormatter'
    )
    @pytest.mark.asyncio
    async def test_execute_tool_loop_with_tool_calls(
        self,
        mock_formatter,
        mock_executor_cls,
        mock_parser,
        mock_invoker_parser,
    ):
        # Setup
        mock_parser.has_tool_calls.side_effect = [
            True,
            False,
        ]  # First call has tools, second has final response
        mock_invoker_parser.get_assistant_message_with_tool_calls.return_value = []

        # Mock tool extraction
        mock_invoker_parser.extract_tool_calls.return_value = [
            {'id': 'call_1', 'name': 'test_tool', 'arguments': {'arg': 'val'}}
        ]

        # Mock tool execution
        mock_executor = Mock()
        mock_executor.execute_tool = AsyncMock()
        mock_executor_cls.return_value = mock_executor
        mock_execution_result = Mock()
        mock_execution_result.success = True
        mock_execution_result.result = 'Tool Result'
        mock_executor.execute_tool.return_value = mock_execution_result

        # Mock responses
        response1 = self._make_response(
            output_text=''
        )  # Tool call response usually has empty text or is ignored
        response2 = self._make_response(
            output_text='Final Answer', usage_attrs={'total_tokens': 200}
        )
        self.mock_client.call_api.side_effect = [response1, response2]

        # Execute
        tools: list[BaseTool] = [cast(BaseTool, Mock(name='test_tool'))]
        response = await self.handler.execute_tool_loop(
            model=OPENAI_MODEL_NANO,
            instructions='Instr',
            messages=[],
            config={},
            tools=tools,
        )

        # Verify
        assert response == 'Final Answer'
        assert self.mock_client.call_api.call_count == 2
        mock_executor.execute_tool.assert_called_with('test_tool', arg='val')

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is True

    @pytest.mark.asyncio
    async def test_execute_tool_loop_composes_real_tool_call_flow(self):
        class EchoTool(BaseTool):
            name = 'echo'
            description = 'Echoes the supplied value'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'value': {
                        'type': 'string',
                        'description': 'Value to echo',
                    }
                },
                'required': ['value'],
            }

            def execute(self, value: str) -> str:
                return f'echo: {value}'

        tool_call_response = SimpleNamespace(
            output=[
                SimpleNamespace(
                    type='function_call',
                    id='fc_123',
                    call_id='call_123',
                    name='echo',
                    arguments='{"value": "protocol input"}',
                )
            ],
            output_text='',
            usage=SimpleNamespace(
                total_tokens=7,
                input_tokens=4,
                output_tokens=3,
            ),
        )
        final_response = SimpleNamespace(
            output=[],
            output_text='Final answer after the tool call.',
            usage=SimpleNamespace(
                total_tokens=9,
                input_tokens=5,
                output_tokens=4,
            ),
        )
        messages = [{'role': 'user', 'content': 'Use the echo tool.'}]
        self.mock_client.call_api.side_effect = [
            tool_call_response,
            final_response,
        ]

        response = await self.handler.execute_tool_loop(
            model=OPENAI_MODEL_NANO,
            instructions='Use tools when needed.',
            messages=messages,
            config={},
            tools=[EchoTool()],
        )

        first_request, second_request = (
            self.mock_client.call_api.await_args_list
        )
        assert response == 'Final answer after the tool call.'
        assert first_request.args[4] == [
            {
                'type': 'function',
                'name': 'echo',
                'description': 'Echoes the supplied value',
                'parameters': EchoTool.parameters,
            }
        ]
        assert second_request.args[2] == [
            {'role': 'user', 'content': 'Use the echo tool.'},
            {
                'type': 'function_call',
                'id': 'fc_123',
                'call_id': 'call_123',
                'name': 'echo',
                'arguments': '{"value": "protocol input"}',
            },
            {
                'type': 'function_call_output',
                'call_id': 'call_123',
                'output': 'echo: protocol input',
            },
        ]

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 16
        assert metrics[0].prompt_tokens == 9
        assert metrics[0].completion_tokens == 7

    @pytest.mark.asyncio
    async def test_invalid_tool_arguments_return_error_output(self):
        class EchoTool(BaseTool):
            name = 'echo'
            description = 'Echoes the supplied value'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'value': {'type': 'string'},
                },
                'required': ['value'],
            }

            def execute(self, value: str) -> str:
                raise AssertionError('The malformed call must not execute')

        malformed_response = SimpleNamespace(
            output=[
                SimpleNamespace(
                    type='function_call',
                    id='fc_bad',
                    call_id='call_bad',
                    name='echo',
                    arguments='{not valid json}',
                )
            ],
            output_text='',
            usage=None,
        )
        final_response = SimpleNamespace(
            output=[],
            output_text='The tool call was corrected.',
            usage=None,
        )
        messages = [{'role': 'user', 'content': 'Use the echo tool.'}]
        self.mock_client.call_api.side_effect = [
            malformed_response,
            final_response,
        ]

        response = await self.handler.execute_tool_loop(
            model=OPENAI_MODEL_NANO,
            instructions='Use tools when needed.',
            messages=messages,
            config={},
            tools=[EchoTool()],
        )

        assert response == 'The tool call was corrected.'
        assert messages[-1]['type'] == 'function_call_output'
        assert messages[-1]['call_id'] == 'call_bad'
        assert 'valid JSON arguments' in messages[-1]['output']
