import ast
import operator
import time
from typing import Any

import pytest

from createagents.domain import BaseTool, ToolExecutionResult, ToolExecutor
from createagents.domain.interfaces import LoggerInterface

# allow-assertion-reduction: Removed batch and parallel executor cases target the retired execution contract; current single-tool behavior is covered below.


def _evaluate_number(node: ast.AST) -> int | float:
    """Evaluate the small arithmetic subset used by the calculator fixture."""
    if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
        return node.value

    binary_operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    if isinstance(node, ast.BinOp) and type(node.op) in binary_operations:
        operation = binary_operations[type(node.op)]
        return operation(
            _evaluate_number(node.left), _evaluate_number(node.right)
        )

    unary_operations = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    if isinstance(node, ast.UnaryOp) and type(node.op) in unary_operations:
        return unary_operations[type(node.op)](_evaluate_number(node.operand))

    raise ValueError('Only numeric arithmetic is supported')


class MockLogger(LoggerInterface):
    """Mock logger for testing purposes."""

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        pass

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        pass

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        pass

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        pass

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        pass


@pytest.fixture
def mock_logger():
    """Fixture to provide a mock logger for tests."""
    return MockLogger()


class MockCalculatorTool(BaseTool):
    name = 'calculator'
    description = 'Performs basic mathematical calculations'
    parameters = {
        'type': 'object',
        'properties': {
            'expression': {
                'type': 'string',
                'description': 'Math expression to evaluate',
            }
        },
        'required': ['expression'],
    }

    def execute(self, expression: str) -> str:
        try:
            tree = ast.parse(expression, mode='eval')
            result = _evaluate_number(tree.body)
            return f'Result: {result}'
        except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as e:
            raise ValueError(f'Invalid expression: {e}') from e


class MockGreeterTool(BaseTool):
    name = 'greeter'
    description = 'Greets people by name'
    parameters = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'description': 'Name to greet'}
        },
        'required': ['name'],
    }

    def execute(self, name: str) -> str:
        return f'Hello, {name}!'


class TestToolExecutor:
    def test_initialization_with_tools(self, mock_logger):
        tools = [MockCalculatorTool(), MockGreeterTool()]
        executor = ToolExecutor(tools, mock_logger)

        assert executor.get_available_tool_names() == ['calculator', 'greeter']

    def test_initialization_without_tools(self, mock_logger):
        executor = ToolExecutor([], mock_logger)

        assert executor.get_available_tool_names() == []

    def test_has_tool(self, mock_logger):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools, mock_logger)

        assert executor.has_tool('calculator') is True
        assert executor.has_tool('nonexistent') is False

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, mock_logger):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('calculator', expression='2 + 2')

        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert result.tool_name == 'calculator'
        assert '4' in result.result
        assert result.error is None
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execute_tool_with_kwargs(self, mock_logger):
        tools = [MockGreeterTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('greeter', name='Alice')

        assert result.success is True
        assert 'Alice' in result.result

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, mock_logger):
        executor = ToolExecutor([], mock_logger)

        result = await executor.execute_tool('nonexistent', arg='value')

        assert result.success is False
        assert result.tool_name == 'nonexistent'
        assert 'not found' in result.error.lower()
        assert result.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_execute_tool_with_invalid_arguments(self, mock_logger):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('calculator')

        assert result.success is False
        assert 'invalid arguments' in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_with_execution_error(self, mock_logger):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool(
            'calculator', expression='invalid + syntax'
        )

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_tool_rejects_non_arithmetic_expression(
        self, mock_logger
    ):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool(
            'calculator', expression="__import__('os').getcwd()"
        )

        assert result.success is False
        assert result.error is not None

    def test_tool_execution_result_to_dict(self):
        result = ToolExecutionResult(
            tool_name='test_tool',
            success=True,
            result='Test result',
            execution_time_ms=123.45,
        )

        result_dict = result.to_dict()

        assert result_dict['tool_name'] == 'test_tool'
        assert result_dict['success'] is True
        assert result_dict['result'] == 'Test result'
        assert result_dict['error'] is None
        assert result_dict['execution_time_ms'] == 123.45

    def test_tool_execution_result_to_llm_message_success(self):
        result = ToolExecutionResult(
            tool_name='calculator', success=True, result='Result: 42'
        )

        message = result.to_llm_message()

        assert 'calculator' in message
        assert 'successfully' in message.lower()
        assert '42' in message

    def test_tool_execution_result_to_llm_message_failure(self):
        result = ToolExecutionResult(
            tool_name='calculator', success=False, error='Invalid input'
        )

        message = result.to_llm_message()

        assert 'calculator' in message
        assert 'failed' in message.lower()
        assert 'Invalid input' in message


@pytest.mark.unit
class TestToolExecutorEdgeCases:
    @pytest.mark.asyncio
    async def test_execute_tool_with_none_value_argument(self, mock_logger):
        class NullableTool(BaseTool):
            name = 'nullable'
            description = 'Accepts None values'

            def execute(self, value=None) -> str:
                return f'Value: {value}'

        tools = [NullableTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('nullable', value=None)

        assert result.success is True
        assert 'None' in result.result

    @pytest.mark.asyncio
    async def test_execute_tool_tracks_execution_time(self, mock_logger):
        class SlowTool(BaseTool):
            name = 'slow'
            description = 'Slow tool'

            def execute(self) -> str:
                time.sleep(0.01)
                return 'done'

        tools = [SlowTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('slow')

        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 10

    @pytest.mark.asyncio
    async def test_execute_tool_tracks_time_on_failure(self, mock_logger):
        class FailingTool(BaseTool):
            name = 'failing'
            description = 'Always fails'

            def execute(self) -> str:
                raise RuntimeError('Tool error')

        tools = [FailingTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('failing')

        assert result.success is False
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execute_tool_with_extra_kwargs(self, mock_logger):
        class SimpleToolWithKwargs(BaseTool):
            name = 'simple'
            description = 'Simple tool'

            def execute(self, arg1: str) -> str:
                return arg1

        tools = [SimpleToolWithKwargs()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool(
            'simple', arg1='value', extra='ignored'
        )

        assert result.success is False
        assert (
            'invalid arguments' in result.error.lower()
            or 'unexpected' in result.error.lower()
        )

    @pytest.mark.asyncio
    async def test_execute_tool_with_complex_return_types(self, mock_logger):
        class ComplexReturnTool(BaseTool):
            name = 'complex'
            description = 'Returns complex data'

            def execute(self) -> dict:
                return {'data': [1, 2, 3], 'nested': {'key': 'value'}}

        tools = [ComplexReturnTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('complex')

        assert result.success is True
        assert isinstance(result.result, dict)

    def test_get_available_tool_names_after_initialization(self, mock_logger):
        class Tool1(BaseTool):
            name = 'tool_one'
            description = 'First tool'

            def execute(self) -> str:
                return 'one'

        class Tool2(BaseTool):
            name = 'tool_two'
            description = 'Second tool'

            def execute(self) -> str:
                return 'two'

        tools = [Tool1(), Tool2()]
        executor = ToolExecutor(tools, mock_logger)

        names = executor.get_available_tool_names()

        assert len(names) == 2
        assert 'tool_one' in names
        assert 'tool_two' in names

    @pytest.mark.asyncio
    async def test_executor_with_duplicate_tool_names(self, mock_logger):
        class Tool1(BaseTool):
            name = 'duplicate'
            description = 'First duplicate'

            def execute(self) -> str:
                return 'first'

        class Tool2(BaseTool):
            name = 'duplicate'
            description = 'Second duplicate'

            def execute(self) -> str:
                return 'second'

        tools = [Tool1(), Tool2()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('duplicate')

        assert result.success is True
        assert result.result == 'second'

    @pytest.mark.asyncio
    async def test_execute_tool_with_unicode_arguments(self, mock_logger):
        class UnicodeTool(BaseTool):
            name = 'unicode'
            description = 'Handles unicode'

            def execute(self, text: str) -> str:
                return f'Received: {text}'

        tools = [UnicodeTool()]
        executor = ToolExecutor(tools, mock_logger)

        result = await executor.execute_tool('unicode', text='你好世界 🌍')

        assert result.success is True
        assert '你好世界' in result.result
        assert '🌍' in result.result

    def test_tool_execution_result_to_dict_with_none_values(self):
        result = ToolExecutionResult(
            tool_name='test',
            success=False,
            result=None,
            error=None,
            execution_time_ms=None,
        )

        result_dict = result.to_dict()

        assert result_dict['result'] is None
        assert result_dict['error'] is None
        assert result_dict['execution_time_ms'] is None
