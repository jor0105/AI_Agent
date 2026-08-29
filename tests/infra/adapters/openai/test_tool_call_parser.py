import json
from typing import Any, cast
from unittest.mock import Mock

import pytest

from createagents.infra import ToolCallParser


class MockOutputItem:
    def __init__(self, type_: str, **kwargs):
        self.type = type_
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockResponse:
    def __init__(self, output: list[Any]):
        self.output = output


@pytest.mark.unit
class TestToolCallParser:
    def test_has_tool_calls_with_no_output(self):
        response = Mock()
        response.output = []

        result = ToolCallParser.has_tool_calls(response)

        assert result is False

    def test_has_tool_calls_with_no_output_attribute(self):
        response = Mock(spec=[])

        result = ToolCallParser.has_tool_calls(response)

        assert result is False

    def test_has_tool_calls_with_function_call_type(self):
        output_item = MockOutputItem(
            'function_call', name='test_tool', call_id='call_123'
        )
        response = MockResponse([output_item])

        result = ToolCallParser.has_tool_calls(response)

        assert result is True

    def test_has_tool_calls_with_mixed_types(self):
        output_items = [
            MockOutputItem('reasoning', summary=['thinking']),
            MockOutputItem(
                'function_call', name='test_tool', call_id='call_123'
            ),
            MockOutputItem('text', content='some text'),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.has_tool_calls(response)

        assert result is True

    def test_has_tool_calls_with_no_function_calls(self):
        output_items = [
            MockOutputItem('reasoning', summary=['thinking']),
            MockOutputItem('text', content='some text'),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.has_tool_calls(response)

        assert result is False

    def test_has_tool_calls_handles_attribute_error(self):
        class BadResponse:
            @property
            def output(self):
                raise AttributeError('No output')

        response = BadResponse()

        result = ToolCallParser.has_tool_calls(response)

        assert result is False

    def test_extract_tool_calls_from_empty_response(self):
        response = MockResponse([])

        result = ToolCallParser.extract_tool_calls(response)

        assert result == []

    def test_extract_tool_calls_with_single_tool(self):
        output_item = MockOutputItem(
            'function_call',
            id='fc_123',
            call_id='call_abc123',
            name='get_weather',
            arguments='{"location": "Paris"}',
        )
        response = MockResponse([output_item])

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['id'] == 'call_abc123'
        assert result[0]['name'] == 'get_weather'
        assert result[0]['arguments'] == {'location': 'Paris'}

    def test_extract_tool_calls_with_multiple_tools(self):
        output_items = [
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='tool_one',
                arguments='{"param": "value1"}',
            ),
            MockOutputItem(
                'function_call',
                id='fc_2',
                call_id='call_2',
                name='tool_two',
                arguments='{"param": "value2"}',
            ),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 2
        assert result[0]['name'] == 'tool_one'
        assert result[1]['name'] == 'tool_two'

    def test_extract_tool_calls_with_dict_arguments(self):
        output_item = MockOutputItem(
            'function_call',
            id='fc_123',
            call_id='call_abc',
            name='test_tool',
            arguments={'key': 'value'},
        )
        response = MockResponse([output_item])

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['arguments'] == {'key': 'value'}

    def test_extract_tool_calls_skips_invalid_json(self):
        output_items = [
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='valid_tool',
                arguments='{"valid": "json"}',
            ),
            MockOutputItem(
                'function_call',
                id='fc_2',
                call_id='call_2',
                name='invalid_tool',
                arguments='{invalid json}',
            ),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['name'] == 'valid_tool'

    def test_extract_tool_calls_skips_non_function_types(self):
        output_items = [
            MockOutputItem('reasoning', summary=['thinking']),
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='tool',
                arguments='{}',
            ),
            MockOutputItem('text', content='text'),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['name'] == 'tool'

    def test_extract_tool_calls_handles_missing_attributes(self):
        output_items = [
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='good_tool',
                arguments='{}',
            ),
            MockOutputItem('function_call'),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['name'] == 'good_tool'

    def test_format_tool_results_for_llm(self):
        result = ToolCallParser.format_tool_results_for_llm(
            tool_call_id='call_abc123',
            tool_name='get_weather',
            result='The weather is 15°C',
        )

        assert result['type'] == 'function_call_output'
        assert result['call_id'] == 'call_abc123'
        assert result['output'] == 'The weather is 15°C'

    def test_format_tool_results_converts_result_to_string(self):
        result = ToolCallParser.format_tool_results_for_llm(
            tool_call_id='call_123',
            tool_name='calculate',
            result=cast(str, 42),
        )

        assert result['output'] == '42'

    def test_format_tool_results_with_empty_result(self):
        result = ToolCallParser.format_tool_results_for_llm(
            tool_call_id='call_123', tool_name='test', result=''
        )

        assert result['output'] == ''

    def test_format_tool_results_with_complex_result(self):
        complex_result = {'data': [1, 2, 3], 'status': 'success'}

        result = ToolCallParser.format_tool_results_for_llm(
            tool_call_id='call_123',
            tool_name='api_call',
            result=cast(str, complex_result),
        )

        assert 'data' in result['output']
        assert 'status' in result['output']

    def test_get_assistant_message_with_tool_calls_returns_none_without_tools(
        self,
    ):
        output_items = [
            MockOutputItem('text', content='Just text'),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is None

    def test_get_assistant_message_with_tool_calls_extracts_reasoning(self):
        output_items = [
            MockOutputItem(
                'reasoning', id='r_123', summary=['Thinking about the problem']
            ),
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='tool',
                arguments='{}',
            ),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is not None
        assert len(result) == 2
        assert result[0]['type'] == 'reasoning'
        assert result[0]['id'] == 'r_123'
        assert result[1]['type'] == 'function_call'

    def test_get_assistant_message_with_tool_calls_extracts_function_calls(
        self,
    ):
        output_item = MockOutputItem(
            'function_call',
            id='fc_123',
            call_id='call_abc',
            name='get_weather',
            arguments='{"location": "Paris"}',
        )
        response = MockResponse([output_item])

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is not None
        assert len(result) == 1
        assert result[0]['type'] == 'function_call'
        assert result[0]['name'] == 'get_weather'
        assert result[0]['call_id'] == 'call_abc'

    def test_get_assistant_message_filters_out_other_types(self):
        output_items = [
            MockOutputItem('text', content='Some text'),
            MockOutputItem('reasoning', id='r_1', summary=['Reasoning']),
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='tool',
                arguments='{}',
            ),
            MockOutputItem('image', url='http://example.com/img.png'),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is not None
        assert len(result) == 2
        assert result[0]['type'] == 'reasoning'
        assert result[1]['type'] == 'function_call'

    def test_get_assistant_message_handles_no_output(self):
        response = Mock(spec=[])

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is None

    def test_get_assistant_message_handles_attribute_error(self):
        class BadResponse:
            @property
            def output(self):
                raise AttributeError('No output')

        response = BadResponse()

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is None

    def test_extract_tool_calls_with_nested_arguments(self):
        nested_args = json.dumps(
            {
                'query': 'test',
                'options': {'limit': 10, 'sort': 'desc'},
                'filters': ['active', 'verified'],
            }
        )

        output_item = MockOutputItem(
            'function_call',
            id='fc_1',
            call_id='call_1',
            name='search',
            arguments=nested_args,
        )
        response = MockResponse([output_item])

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['arguments']['query'] == 'test'
        assert result[0]['arguments']['options']['limit'] == 10
        assert result[0]['arguments']['filters'] == ['active', 'verified']

    def test_extract_tool_calls_with_empty_arguments(self):
        output_item = MockOutputItem(
            'function_call',
            id='fc_1',
            call_id='call_1',
            name='no_params_tool',
            arguments='{}',
        )
        response = MockResponse([output_item])

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]['arguments'] == {}

    def test_has_tool_calls_with_none_output(self):
        response = Mock()
        response.output = None

        result = ToolCallParser.has_tool_calls(response)

        assert result is False

    def test_get_assistant_message_returns_none_for_empty_list(self):
        response = MockResponse([MockOutputItem('text', content='Only text')])

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is None

    def test_extract_tool_calls_logs_on_json_error(self, caplog):
        import logging

        caplog.set_level(logging.ERROR)

        output_item = MockOutputItem(
            'function_call',
            id='fc_1',
            call_id='call_1',
            name='bad_tool',
            arguments='{not valid json}',
        )
        response = MockResponse([output_item])

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 0

    def test_format_tool_results_with_multiline_result(self):
        multiline_result = """Line 1
Line 2
Line 3"""

        result = ToolCallParser.format_tool_results_for_llm(
            tool_call_id='call_123', tool_name='test', result=multiline_result
        )

        assert '\n' in result['output']
        assert 'Line 1' in result['output']

    def test_extract_tool_calls_preserves_order(self):
        output_items = [
            MockOutputItem(
                'function_call',
                id='fc_1',
                call_id='call_1',
                name='first_tool',
                arguments='{}',
            ),
            MockOutputItem(
                'function_call',
                id='fc_2',
                call_id='call_2',
                name='second_tool',
                arguments='{}',
            ),
            MockOutputItem(
                'function_call',
                id='fc_3',
                call_id='call_3',
                name='third_tool',
                arguments='{}',
            ),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 3
        assert result[0]['name'] == 'first_tool'
        assert result[1]['name'] == 'second_tool'
        assert result[2]['name'] == 'third_tool'

    def test_get_assistant_message_preserves_item_structure(self):
        output_items = [
            MockOutputItem(
                'reasoning',
                id='r_123',
                summary=['Step 1', 'Step 2'],
            ),
            MockOutputItem(
                'function_call',
                id='fc_456',
                call_id='call_789',
                name='tool_name',
                arguments='{"param": "value"}',
            ),
        ]
        response = MockResponse(output_items)

        result = ToolCallParser.get_assistant_message_with_tool_calls(response)

        assert result is not None
        assert result[0]['id'] == 'r_123'
        assert result[0]['summary'] == ['Step 1', 'Step 2']
        assert result[1]['id'] == 'fc_456'
        assert result[1]['call_id'] == 'call_789'

    def test_extract_tool_calls_with_unicode_in_arguments(self):
        unicode_args = json.dumps(
            {'text': 'Olá, 你好, مرحبا', 'emoji': '🎉🚀'}
        )

        output_item = MockOutputItem(
            'function_call',
            id='fc_1',
            call_id='call_1',
            name='unicode_tool',
            arguments=unicode_args,
        )
        response = MockResponse([output_item])

        result = ToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert 'Olá' in result[0]['arguments']['text']
        assert '🎉' in result[0]['arguments']['emoji']
