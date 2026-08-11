from unittest.mock import patch

import pytest

from createagents.domain import BaseTool
from createagents.infra import AvailableTools, CurrentDateTool

LAZY_CACHE = '_AvailableTools__LAZY_SYSTEM_TOOLS'
LAZY_LOADER = '_AvailableTools__try_load_read_local_file_tool'


@pytest.mark.unit
class TestSystemTools:
    def setup_method(self):
        getattr(AvailableTools, LAZY_CACHE).clear()

    def test_returns_a_name_to_description_mapping(self):
        tools = AvailableTools.get_system_tools()

        assert isinstance(tools, dict)
        assert all(isinstance(name, str) for name in tools)
        assert all(isinstance(desc, str) for desc in tools.values())

    def test_includes_the_built_in_currentdate_tool(self):
        tools = AvailableTools.get_system_tools()

        assert 'currentdate' in tools
        assert tools['currentdate'].strip()

    def test_every_description_is_non_empty(self):
        for name, description in AvailableTools.get_system_tools().items():
            assert description.strip(), f'{name} has an empty description'

    def test_names_are_lowercase(self):
        for name in AvailableTools.get_system_tools():
            assert name == name.lower()

    def test_returned_dict_is_a_copy(self):
        tools = AvailableTools.get_system_tools()
        tools['injected'] = 'not a real tool'

        assert 'injected' not in AvailableTools.get_system_tools()


@pytest.mark.unit
class TestToolInstances:
    def setup_method(self):
        getattr(AvailableTools, LAZY_CACHE).clear()

    def test_get_tool_instance_returns_the_registered_tool(self):
        tool = AvailableTools.get_tool_instance('currentdate')

        assert isinstance(tool, CurrentDateTool)

    def test_get_tool_instance_is_case_insensitive(self):
        assert AvailableTools.get_tool_instance('CurrentDate') is not None
        assert AvailableTools.get_tool_instance('CURRENTDATE') is not None

    def test_get_tool_instance_returns_none_for_unknown_name(self):
        assert AvailableTools.get_tool_instance('does_not_exist') is None

    def test_all_instances_implement_base_tool(self):
        instances = AvailableTools.get_all_tool_instances()

        assert instances
        assert all(isinstance(t, BaseTool) for t in instances.values())

    def test_instance_keys_match_the_described_tools(self):
        assert set(AvailableTools.get_all_tool_instances()) == set(
            AvailableTools.get_system_tools()
        )

    def test_mutating_the_returned_dict_does_not_affect_the_registry(self):
        instances = AvailableTools.get_all_tool_instances()
        instances.pop('currentdate')

        assert 'currentdate' in AvailableTools.get_all_tool_instances()


@pytest.mark.unit
class TestLazyLoading:
    def setup_method(self):
        getattr(AvailableTools, LAZY_CACHE).clear()

    def test_reading_the_catalog_attempts_the_lazy_load(self):
        with patch.object(AvailableTools, LAZY_LOADER) as mock_load:
            AvailableTools.get_system_tools()

        assert mock_load.called

    def test_lazy_load_runs_only_once(self):
        AvailableTools.get_system_tools()

        with patch(
            'createagents.infra.adapters.Tools.Read_Local_File_Tool'
            '.read_local_file_tool.ReadLocalFileTool'
        ) as mock_tool:
            AvailableTools.get_system_tools()

        assert not mock_tool.called

    def test_missing_optional_dependencies_do_not_break_the_catalog(self):
        getattr(AvailableTools, LAZY_CACHE).clear()

        with patch(
            'createagents.infra.adapters.Tools.available_tools.AvailableTools'
            '._AvailableTools__try_load_read_local_file_tool',
            side_effect=lambda: getattr(AvailableTools, LAZY_CACHE).update(
                {'readlocalfile': None}
            ),
        ):
            tools = AvailableTools.get_system_tools()

        assert 'currentdate' in tools
        assert 'readlocalfile' not in tools

    def test_unavailable_tool_is_not_offered_as_an_instance(self):
        getattr(AvailableTools, LAZY_CACHE)['readlocalfile'] = None

        assert AvailableTools.get_tool_instance('readlocalfile') is None
