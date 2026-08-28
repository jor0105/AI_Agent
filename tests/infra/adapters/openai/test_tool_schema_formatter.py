from typing import ClassVar

import pytest

from createagents.domain import BaseTool
from createagents.infra import ToolSchemaFormatter

# allow-assertion-reduction: Removed chat-completions formatter cases target the retired API format; Responses API coverage remains below.


class MockWeatherTool(BaseTool):
    name = 'get_weather'
    description = 'Get the current weather for a location'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {
            'location': {
                'type': 'string',
                'description': 'The city and state, e.g. San Francisco, CA',
            },
            'unit': {
                'type': 'string',
                'enum': ['celsius', 'fahrenheit'],
                'description': 'Temperature unit',
            },
        },
        'required': ['location'],
    }

    def execute(self, location: str, unit: str = 'celsius') -> str:
        return f'Weather in {location}: 15°{unit[0].upper()}'


class MockSearchTool(BaseTool):
    name = 'web_search'
    description = 'Search the web for information'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The search query',
            }
        },
        'required': ['query'],
    }

    def execute(self, query: str) -> str:
        return f'Search results for: {query}'


class MockNoParamsTool(BaseTool):
    name = 'get_time'
    description = 'Get the current time'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {},
        'required': [],
    }

    def execute(self) -> str:
        return '12:00 PM'


@pytest.mark.unit
class TestToolSchemaFormatter:
    def test_format_tool_for_responses_api(self):
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result['type'] == 'function'
        assert result['name'] == 'web_search'
        assert result['description'] == 'Search the web for information'
        assert 'parameters' in result

    def test_format_tool_for_responses_api_includes_parameters(self):
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert 'query' in params['properties']
        assert params['required'] == ['query']

    def test_format_tools_for_responses_api_single_tool(self):
        tools = [MockSearchTool()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 1
        assert result[0]['type'] == 'function'
        assert result[0]['name'] == 'web_search'

    def test_format_tools_for_responses_api_multiple_tools(self):
        tools = [MockWeatherTool(), MockSearchTool()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 2
        names = [tool['name'] for tool in result]
        assert 'get_weather' in names
        assert 'web_search' in names

    def test_format_tool_with_no_parameters(self):
        tool = MockNoParamsTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result['parameters']['properties'] == {}

    def test_format_tools_for_responses_api_empty_list(self):
        tools = []

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert result == []

    def test_format_preserves_parameter_types(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        location_prop = result['parameters']['properties']['location']
        unit_prop = result['parameters']['properties']['unit']

        assert location_prop['type'] == 'string'
        assert unit_prop['type'] == 'string'
        assert unit_prop['enum'] == ['celsius', 'fahrenheit']

    def test_format_preserves_descriptions(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert (
            result['description'] == 'Get the current weather for a location'
        )
        location_desc = result['parameters']['properties']['location'][
            'description'
        ]
        assert 'city and state' in location_desc

    def test_format_preserves_required_fields(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result['parameters']['required'] == ['location']

    def test_format_tools_maintains_order(self):
        tools = [
            MockWeatherTool(),
            MockSearchTool(),
            MockNoParamsTool(),
        ]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert result[0]['name'] == 'get_weather'
        assert result[1]['name'] == 'web_search'
        assert result[2]['name'] == 'get_time'

    def test_format_tool_with_complex_parameters(self):
        class ComplexTool(BaseTool):
            name = 'complex_search'
            description = 'Advanced search with filters'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'filters': {
                        'type': 'object',
                        'properties': {
                            'date_from': {'type': 'string'},
                            'date_to': {'type': 'string'},
                            'categories': {
                                'type': 'array',
                                'items': {'type': 'string'},
                            },
                        },
                    },
                    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100},
                },
                'required': ['query'],
            }

            def execute(self, **kwargs):
                return 'results'

        tool = ComplexTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert 'filters' in result['parameters']['properties']
        assert (
            'date_from'
            in result['parameters']['properties']['filters']['properties']
        )
        assert result['parameters']['properties']['limit']['minimum'] == 1

    def test_format_tool_preserves_enum_values(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        unit_enum = result['parameters']['properties']['unit']['enum']
        assert unit_enum == ['celsius', 'fahrenheit']

    def test_format_tool_with_special_characters_in_description(self):
        class SpecialTool(BaseTool):
            name = 'special_tool'
            description = (
                'Tool with special chars: @#$%^&*() and unicode: 你好'
            )
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {},
            }

            def execute(self):
                return 'ok'

        tool = SpecialTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert '你好' in result['description']
        assert '@#$%^&*()' in result['description']

    def test_format_tools_for_responses_api_logs_count(self, caplog):
        import logging

        caplog.set_level(logging.INFO)

        tools = [MockWeatherTool(), MockSearchTool()]

        formatted = ToolSchemaFormatter.format_tools_for_responses_api(tools)
        assert len(formatted) == 2
        assert any('2' in record.message for record in caplog.records)

    def test_format_tool_with_array_parameter(self):
        class ArrayTool(BaseTool):
            name = 'multi_search'
            description = 'Search multiple queries'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'queries': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'List of search queries',
                    }
                },
                'required': ['queries'],
            }

            def execute(self, queries):
                return f'Searching: {queries}'

        tool = ArrayTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        queries_prop = result['parameters']['properties']['queries']
        assert queries_prop['type'] == 'array'
        assert queries_prop['items']['type'] == 'string'

    def test_format_tool_with_number_parameters(self):
        class MathTool(BaseTool):
            name = 'calculate'
            description = 'Perform calculations'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'a': {'type': 'number', 'description': 'First number'},
                    'b': {'type': 'integer', 'description': 'Second number'},
                },
                'required': ['a', 'b'],
            }

            def execute(self, a, b):
                return a + b

        tool = MathTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result['parameters']['properties']['a']['type'] == 'number'
        assert result['parameters']['properties']['b']['type'] == 'integer'

    def test_format_tool_with_boolean_parameter(self):
        class FlagTool(BaseTool):
            name = 'search_with_flag'
            description = 'Search with optional flag'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'exact_match': {
                        'type': 'boolean',
                        'description': 'Use exact matching',
                    },
                },
                'required': ['query'],
            }

            def execute(self, query, exact_match=False):
                return f'Searching: {query} (exact={exact_match})'

        tool = FlagTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        exact_match_prop = result['parameters']['properties']['exact_match']
        assert exact_match_prop['type'] == 'boolean'

    def test_format_multiple_tools_with_same_parameter_names(self):
        class Tool1(BaseTool):
            name = 'tool_one'
            description = 'First tool'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {'param': {'type': 'string'}},
            }

            def execute(self, param):
                return param

        class Tool2(BaseTool):
            name = 'tool_two'
            description = 'Second tool'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {'param': {'type': 'integer'}},
            }

            def execute(self, param):
                return param

        tools = [Tool1(), Tool2()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 2
        assert (
            result[0]['parameters']['properties']['param']['type'] == 'string'
        )
        assert (
            result[1]['parameters']['properties']['param']['type'] == 'integer'
        )

    def test_responses_format_has_flat_structure(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert 'type' in result
        assert 'name' in result
        assert 'description' in result
        assert 'parameters' in result
        assert 'function' not in result

    def test_format_tool_schema_is_valid_json_schema(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert isinstance(params['properties'], dict)
        assert isinstance(params.get('required', []), list)

    def test_format_preserves_additional_schema_properties(self):
        class ValidationTool(BaseTool):
            name = 'validate_input'
            description = 'Validate input with constraints'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                        'minLength': 5,
                        'maxLength': 100,
                        'pattern': '^[a-zA-Z]+$',
                    }
                },
                'required': ['text'],
            }

            def execute(self, text):
                return f'Valid: {text}'

        tool = ValidationTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        text_prop = result['parameters']['properties']['text']
        assert text_prop['minLength'] == 5
        assert text_prop['maxLength'] == 100
        assert text_prop['pattern'] == '^[a-zA-Z]+$'
