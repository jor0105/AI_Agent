from typing import ClassVar

from createagents.domain import BaseTool
from createagents.infra import OllamaToolSchemaFormatter


class MockTool(BaseTool):
    name = 'mock_tool'
    description = 'A mock tool for testing'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {
            'param1': {'type': 'string', 'description': 'First parameter'}
        },
        'required': ['param1'],
    }

    def execute(self, param1: str) -> str:
        return f'Executed with {param1}'


def test_format_single_tool():
    tool = MockTool()
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

    assert len(formatted) == 1
    assert formatted[0]['type'] == 'function'
    assert formatted[0]['function']['name'] == 'mock_tool'
    assert formatted[0]['function']['description'] == 'A mock tool for testing'
    assert 'parameters' in formatted[0]['function']


def test_format_multiple_tools():
    class Tool1(BaseTool):
        name = 'tool1'
        description = 'First tool'
        parameters: ClassVar[dict[str, object]] = {
            'type': 'object',
            'properties': {},
        }

        def execute(self):
            return 'result1'

    class Tool2(BaseTool):
        name = 'tool2'
        description = 'Second tool'
        parameters: ClassVar[dict[str, object]] = {
            'type': 'object',
            'properties': {},
        }

        def execute(self):
            return 'result2'

    tools = [Tool1(), Tool2()]
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama(tools)

    assert len(formatted) == 2
    assert formatted[0]['function']['name'] == 'tool1'
    assert formatted[1]['function']['name'] == 'tool2'


def test_format_empty_tools_list():
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([])
    assert formatted == []


def test_tool_schema_structure():
    tool = MockTool()
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

    expected_structure = {
        'type': 'function',
        'function': {
            'name': 'mock_tool',
            'description': 'A mock tool for testing',
            'parameters': {
                'type': 'object',
                'properties': {
                    'param1': {
                        'type': 'string',
                        'description': 'First parameter',
                    }
                },
                'required': ['param1'],
            },
        },
    }

    assert formatted[0] == expected_structure


def test_tool_parameters_preserved():
    tool = MockTool()
    formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

    params = formatted[0]['function']['parameters']
    assert params['type'] == 'object'
    assert 'param1' in params['properties']
    assert params['properties']['param1']['type'] == 'string'
    assert 'required' in params
    assert 'param1' in params['required']
