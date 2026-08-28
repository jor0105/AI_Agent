from unittest.mock import Mock

import pytest

from createagents.application import GetSystemAvailableToolsUseCase
from createagents.application.interfaces import ToolRegistry


@pytest.mark.unit
class TestGetSystemAvailableToolsUseCase:
    def test_execute_returns_dict(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {'tool1': 'desc1'}
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        assert isinstance(result, dict)

    def test_execute_returns_non_empty_dict(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {'tool1': 'desc1'}
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        assert len(result) > 0

    def test_execute_contains_currentdate_tool(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {
            'currentdate': 'Gets current date'
        }
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        assert 'currentdate' in result

    def test_execute_tool_descriptions_are_strings(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {
            'tool1': 'desc1',
            'tool2': 'desc2',
        }
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        for tool_name, tool_description in result.items():
            assert isinstance(tool_name, str)
            assert isinstance(tool_description, str)
            assert len(tool_description) > 0

    def test_execute_returns_consistent_results(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {'tool1': 'desc1'}
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result1 = use_case.execute()
        result2 = use_case.execute()
        assert result1 == result2

    def test_currentdate_tool_description(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {
            'currentdate': 'Gets current date'
        }
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        assert 'currentdate' in result
        assert isinstance(result['currentdate'], str)
        assert len(result['currentdate']) > 0

    def test_execute_tool_names_are_strings(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {
            'tool1': 'desc1',
            'tool2': 'desc2',
        }
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        for tool_name in result:
            assert isinstance(tool_name, str)
            assert len(tool_name) > 0

    def test_execute_with_empty_tools(self):
        registry = Mock(spec=ToolRegistry)
        registry.get_system_tools.return_value = {}
        use_case = GetSystemAvailableToolsUseCase(tool_registry=registry)
        result = use_case.execute()
        assert result == {}
