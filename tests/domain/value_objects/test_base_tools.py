from typing import ClassVar, cast

import pytest

from createagents.domain import BaseTool
from tests.typing_helpers import invoke


class ConcreteTestTool(BaseTool):
    name = 'test_tool'
    description = 'A tool for testing purposes'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {
            'input': {
                'type': 'string',
                'description': 'Test input',
            }
        },
        'required': ['input'],
    }

    def execute(self, input: str) -> str:
        return f'Executed with: {input}'


class MinimalTestTool(BaseTool):
    name = 'minimal_tool'
    description = 'Minimal tool implementation'

    def execute(self) -> str:
        return 'Minimal execution'


class ComplexParametersTool(BaseTool):
    name = 'complex_tool'
    description = 'Tool with complex parameters'
    parameters: ClassVar[dict[str, object]] = {
        'type': 'object',
        'properties': {
            'query': {'type': 'string', 'description': 'Search query'},
            'limit': {
                'type': 'integer',
                'description': 'Result limit',
                'default': 10,
            },
            'filters': {
                'type': 'object',
                'properties': {
                    'category': {'type': 'string'},
                    'date_range': {
                        'type': 'object',
                        'properties': {
                            'start': {'type': 'string'},
                            'end': {'type': 'string'},
                        },
                    },
                },
            },
        },
        'required': ['query'],
    }

    def execute(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, object] | None = None,
    ) -> str:
        return f'Query: {query}, Limit: {limit}, Filters: {filters}'


@pytest.mark.unit
class TestBaseTool:
    def test_cannot_instantiate_base_tool_directly(self):
        with pytest.raises(
            TypeError, match="Can't instantiate abstract class"
        ):
            invoke(BaseTool)

    def test_concrete_implementation_can_be_instantiated(self):
        tool = ConcreteTestTool()

        assert isinstance(tool, BaseTool)
        assert tool.name == 'test_tool'
        assert tool.description == 'A tool for testing purposes'

    def test_execute_method_is_required(self):
        with pytest.raises(TypeError):

            class IncompleteToolNoExecute(BaseTool):
                name = 'incomplete'
                description = 'No execute method'

            invoke(IncompleteToolNoExecute)

    # assertion-reduction-reason: exact schema values replace presence checks.
    def test_name_attribute_is_accessible(self):
        tool = ConcreteTestTool()
        assert tool.name == 'test_tool'
        assert tool.get_schema()['name'] == 'test_tool'

    def test_description_attribute_is_accessible(self):
        tool = ConcreteTestTool()
        assert tool.description == 'A tool for testing purposes'
        assert (
            tool.get_schema()['description'] == 'A tool for testing purposes'
        )

    def test_parameters_attribute_is_accessible(self):
        tool = ConcreteTestTool()
        schema = tool.get_schema()
        assert isinstance(tool.parameters, dict)
        assert schema['parameters']['type'] == 'object'
        assert 'properties' in schema['parameters']

    def test_default_parameters_schema(self):
        tool = MinimalTestTool()

        assert tool.parameters == {'type': 'object', 'properties': {}}

    def test_execute_method_can_be_called(self):
        tool = ConcreteTestTool()

        result = tool.execute(input='test')

        assert result == 'Executed with: test'
        assert isinstance(result, str)

    def test_execute_with_no_arguments(self):
        tool = MinimalTestTool()

        result = tool.execute()

        assert result == 'Minimal execution'

    def test_execute_with_multiple_arguments(self):
        tool = ComplexParametersTool()

        result = tool.execute(
            query='search term', limit=5, filters={'category': 'tech'}
        )

        assert 'search term' in result
        assert '5' in result
        assert 'tech' in result


@pytest.mark.unit
class TestGetSchema:
    def test_get_schema_returns_dict(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert isinstance(schema, dict)

    def test_get_schema_contains_name(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert 'name' in schema
        assert schema['name'] == tool.name

    def test_get_schema_contains_description(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert 'description' in schema
        assert schema['description'] == tool.description

    def test_get_schema_contains_parameters(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert 'parameters' in schema
        assert schema['parameters'] == tool.parameters

    def test_get_schema_has_all_required_fields(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert set(schema.keys()) == {'name', 'description', 'parameters'}

    def test_get_schema_with_minimal_tool(self):
        tool = MinimalTestTool()

        schema = tool.get_schema()

        assert schema['name'] == 'minimal_tool'
        assert schema['description'] == 'Minimal tool implementation'
        assert schema['parameters'] == {'type': 'object', 'properties': {}}

    def test_get_schema_with_complex_parameters(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()

        assert 'query' in schema['parameters']['properties']
        assert 'limit' in schema['parameters']['properties']
        assert 'filters' in schema['parameters']['properties']
        assert 'required' in schema['parameters']
        assert 'query' in schema['parameters']['required']

    def test_get_schema_returns_copy(self):
        tool = ConcreteTestTool()

        schema1 = tool.get_schema()
        schema2 = tool.get_schema()

        assert schema1 == schema2
        assert schema1 is not schema2

    def test_get_schema_can_be_modified_without_affecting_tool(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()
        schema['name'] = 'modified_name'

        assert tool.name == 'test_tool'
        new_schema = tool.get_schema()
        assert new_schema['name'] == 'test_tool'

    def test_get_schema_with_nested_parameters(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        filters = schema['parameters']['properties']['filters']

        assert 'properties' in filters
        assert 'category' in filters['properties']
        assert 'date_range' in filters['properties']


@pytest.mark.unit
class TestToolInheritance:
    def test_multiple_tools_have_independent_schemas(self):
        tool1 = ConcreteTestTool()
        tool2 = MinimalTestTool()

        schema1 = tool1.get_schema()
        schema2 = tool2.get_schema()

        assert schema1['name'] != schema2['name']
        assert schema1['description'] != schema2['description']

    def test_tool_can_be_subclassed_further(self):
        class ExtendedTool(ConcreteTestTool):
            name = 'extended_tool'
            description = 'Extended version'

            def execute(self, input: str) -> str:
                return f'Extended: {super().execute(input)}'

        tool = ExtendedTool()

        assert tool.name == 'extended_tool'
        result = tool.execute(input='test')
        assert 'Extended' in result
        assert 'Executed with: test' in result

    def test_tools_are_isinstance_of_basetool(self):
        tools = [
            ConcreteTestTool(),
            MinimalTestTool(),
            ComplexParametersTool(),
        ]

        for tool in tools:
            assert isinstance(tool, BaseTool)

    def test_tool_attributes_are_class_attributes(self):
        assert ConcreteTestTool.name == 'test_tool'
        assert isinstance(ConcreteTestTool.description, str)
        assert isinstance(ConcreteTestTool.parameters, dict)

    def test_default_parameters_can_be_overridden(self):
        class CustomParamsTool(BaseTool):
            name = 'custom'
            description = 'Custom parameters'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'custom',
                'properties': {'x': {'type': 'number'}},
            }

            def execute(self) -> str:
                return 'custom'

        tool = CustomParamsTool()

        assert tool.parameters['type'] == 'custom'
        properties = cast(dict[str, object], tool.parameters['properties'])
        assert 'x' in properties


@pytest.mark.unit
class TestToolParameterSchemas:
    def test_parameters_follow_json_schema_structure(self):
        tool = ConcreteTestTool()

        params = tool.parameters
        assert params['type'] == 'object'
        assert isinstance(params['properties'], dict)

    def test_parameters_with_required_fields(self):
        tool = ConcreteTestTool()

        params = tool.parameters
        assert 'required' in params
        assert isinstance(params['required'], list)
        assert 'input' in params['required']

    def test_parameters_with_optional_fields(self):
        tool = ComplexParametersTool()

        params = tool.parameters
        required = params.get('required', [])
        all_props = cast(dict[str, object], params['properties']).keys()
        required_names = cast(list[str], required)

        optional = set(all_props) - set(required_names)
        assert 'limit' in optional or 'filters' in optional

    def test_parameters_with_default_values(self):
        tool = ComplexParametersTool()

        properties = cast(
            dict[str, dict[str, object]], tool.parameters['properties']
        )
        limit_param = properties['limit']
        assert 'default' in limit_param
        assert limit_param['default'] == 10

    def test_parameters_with_nested_objects(self):
        tool = ComplexParametersTool()

        properties = cast(
            dict[str, dict[str, object]], tool.parameters['properties']
        )
        filters = properties['filters']
        assert filters['type'] == 'object'
        assert 'properties' in filters

        nested_properties = cast(
            dict[str, dict[str, object]], filters['properties']
        )
        date_range = nested_properties['date_range']
        assert date_range['type'] == 'object'
        assert 'properties' in date_range


@pytest.mark.unit
class TestToolExecution:
    def test_execute_returns_value(self):
        tool = ConcreteTestTool()

        result = tool.execute(input='test')

        assert result is not None

    def test_execute_with_different_inputs(self):
        tool = ConcreteTestTool()

        inputs = ['simple', 'with spaces', 'special!@#$%', '123', '']
        for inp in inputs:
            result = tool.execute(input=inp)
            assert inp in result

    def test_execute_can_raise_exceptions(self):
        class StrictTool(BaseTool):
            name = 'strict'
            description = 'Raises on empty input'

            def execute(self, value: str) -> str:
                if not value:
                    raise ValueError('Value cannot be empty')
                return value

        tool = StrictTool()

        with pytest.raises(ValueError, match='cannot be empty'):
            tool.execute(value='')

    def test_execute_with_kwargs(self):
        tool = ComplexParametersTool()

        result = tool.execute(query='test', limit=20)

        assert 'test' in result
        assert '20' in result

    def test_execute_with_default_arguments(self):
        tool = ComplexParametersTool()

        result = tool.execute(query='test')

        assert 'test' in result
        assert '10' in result


@pytest.mark.unit
class TestToolDocumentation:
    def test_description_is_informative(self):
        tool = ConcreteTestTool()

        assert len(tool.description) > 10
        assert (
            tool.description != 'Base tool description (should be overridden)'
        )

    def test_parameter_descriptions_exist(self):
        tool = ConcreteTestTool()

        properties = cast(
            dict[str, dict[str, object]], tool.parameters['properties']
        )
        for prop in properties.values():
            assert 'description' in prop
            description = prop['description']
            assert isinstance(description, str)
            assert len(description) > 0

    def test_complex_tool_has_detailed_schema(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        assert len(schema['parameters']['properties']) >= 3
        assert 'required' in schema['parameters']


@pytest.mark.unit
class TestToolEdgeCases:
    def test_tool_with_empty_parameters(self):
        class NoParamsTool(BaseTool):
            name = 'no_params'
            description = 'Tool with no parameters'
            parameters: ClassVar[dict[str, object]] = {
                'type': 'object',
                'properties': {},
            }

            def execute(self) -> str:
                return 'no params'

        tool = NoParamsTool()
        schema = tool.get_schema()

        assert schema['parameters']['properties'] == {}

    def test_tool_name_with_special_characters(self):
        class SpecialNameTool(BaseTool):
            name = 'special_tool_123'
            description = 'Tool with special name'

            def execute(self) -> str:
                return 'special'

        tool = SpecialNameTool()

        assert tool.name == 'special_tool_123'
        assert '_' in tool.name
        assert '123' in tool.name

    def test_tool_with_long_description(self):
        long_desc = 'A' * 1000

        class LongDescTool(BaseTool):
            name = 'long_desc'
            description = long_desc

            def execute(self) -> str:
                return 'long'

        tool = LongDescTool()

        assert len(tool.description) == 1000
        assert tool.description == long_desc

    def test_tool_execute_returns_different_types(self):
        class StringTool(BaseTool):
            name = 'string_tool'
            description = 'Returns string'

            def execute(self) -> str:
                return 'string result'

        class DictTool(BaseTool):
            name = 'dict_tool'
            description = 'Returns dict'

            def execute(self) -> dict[str, str]:
                return {'key': 'value'}

        string_tool = StringTool()
        dict_tool = DictTool()

        assert isinstance(string_tool.execute(), str)
        assert isinstance(dict_tool.execute(), dict)

    def test_multiple_tool_instances_are_independent(self):
        tool1 = ConcreteTestTool()
        tool2 = ConcreteTestTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.get_schema() == tool2.get_schema()
