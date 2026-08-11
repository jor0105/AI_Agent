from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from createagents.domain import ChatException
from createagents.infra.adapters.OpenAI.openai_handler import OpenAIHandler

IA_OPENAI_TEST_1: str = 'gpt-5-nano'


@pytest.mark.unit
class TestOpenAIHandler:
    def setup_method(self):
        self.mock_client = Mock()
        self.mock_client.call_api = AsyncMock()
        self.handler = OpenAIHandler(self.mock_client)

    def _make_response(
        self, output_text='', tool_calls=None, usage_attrs=None
    ):
        mock_response = MagicMock()
        mock_response.output_text = output_text

        if tool_calls:
            # Mocking tool calls structure for Responses API
            # This depends on how ToolCallParser expects it
            # Assuming ToolCallParser.has_tool_calls checks for tool_calls attribute or similar
            # Based on openai_chat_adapter.py: ToolCallParser.has_tool_calls(response_api)
            # And ToolCallParser.extract_tool_calls(response_api)
            # I should probably mock ToolCallParser methods instead of response structure if possible,
            # or match what ToolCallParser expects.
            pass

        if usage_attrs:
            mock_usage = MagicMock()
            for k, v in usage_attrs.items():
                setattr(mock_usage, k, v)
            mock_response.usage = mock_usage
        else:
            mock_response.usage = None

        return mock_response

    @patch('createagents.infra.adapters.OpenAI.openai_handler.ToolCallParser')
    @pytest.mark.asyncio
    async def test_execute_tool_loop_success(self, mock_parser):
        mock_parser.has_tool_calls.return_value = False

        mock_response = self._make_response(
            output_text='Success response', usage_attrs={'total_tokens': 100}
        )
        self.mock_client.call_api.return_value = mock_response

        response = await self.handler.execute_tool_loop(
            model=IA_OPENAI_TEST_1,
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

    @patch('createagents.infra.adapters.OpenAI.openai_handler.ToolCallParser')
    @pytest.mark.asyncio
    async def test_execute_tool_loop_empty_response(self, mock_parser):
        mock_parser.has_tool_calls.return_value = False

        mock_response = self._make_response(output_text='')
        self.mock_client.call_api.return_value = mock_response

        with pytest.raises(
            ChatException, match='OpenAI returned an empty response'
        ):
            await self.handler.execute_tool_loop(
                model=IA_OPENAI_TEST_1,
                instructions='Instr',
                messages=[],
                config={},
                tools=None,
            )

    @patch('createagents.infra.adapters.OpenAI.openai_handler.ToolCallParser')
    @pytest.mark.asyncio
    async def test_execute_tool_loop_api_error(self, mock_parser):
        self.mock_client.call_api.side_effect = RuntimeError('API Error')

        with pytest.raises(
            ChatException, match='Error communicating with OpenAI'
        ):
            await self.handler.execute_tool_loop(
                model=IA_OPENAI_TEST_1,
                instructions='Instr',
                messages=[],
                config={},
                tools=None,
            )

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is False
        assert 'API Error' in metrics[0].error_message

    @patch(
        'createagents.infra.adapters.OpenAI.openai_tool_invoker.ToolCallParser'
    )
    @patch('createagents.infra.adapters.OpenAI.openai_handler.ToolCallParser')
    @patch('createagents.infra.adapters.Common.tool_session.ToolExecutor')
    @patch(
        'createagents.infra.adapters.OpenAI.openai_handler.ToolSchemaFormatter'
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
        tools = [Mock(name='test_tool')]
        response = await self.handler.execute_tool_loop(
            model=IA_OPENAI_TEST_1,
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
