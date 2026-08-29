import builtins
import importlib
import logging
import sys
import types

import pytest

from createagents.domain import BaseTool
from createagents.infra import CurrentDateTool

AVAILABLE_TOOLS_MODULE = 'createagents.infra.adapters.tools.available_tools'
OPTIONAL_TOOL_MODULE = 'createagents.infra.adapters.tools.read_local_file_tool'


@pytest.fixture
def available_tools():
    """Return a freshly reloaded catalog with isolated class state."""
    module = importlib.import_module(AVAILABLE_TOOLS_MODULE)
    return importlib.reload(module).AvailableTools


@pytest.fixture
def fake_read_local_file_tool(monkeypatch):
    """Install a public fake optional-tool module for lazy-load tests."""

    class FakeReadLocalFileTool(BaseTool):
        name = 'readlocalfile'
        description = 'A fake local-file tool for catalog tests.'
        construction_count = 0

        def __init__(self) -> None:
            type(self).construction_count += 1

        def execute(self, **kwargs: object) -> str:
            return 'fake file content'

    fake_module = types.ModuleType(OPTIONAL_TOOL_MODULE)
    fake_module.__dict__['ReadLocalFileTool'] = FakeReadLocalFileTool
    monkeypatch.setitem(sys.modules, OPTIONAL_TOOL_MODULE, fake_module)
    return FakeReadLocalFileTool


@pytest.fixture
def missing_read_local_file_tool(monkeypatch):
    """Make the optional-tool import fail as missing dependencies would."""
    original_import = builtins.__import__

    def failing_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 1 and name == 'read_local_file_tool':
            raise ImportError('optional file-tool dependencies unavailable')
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', failing_import)


@pytest.mark.unit
class TestSystemTools:
    def test_returns_a_name_to_description_mapping(self, available_tools):
        tools = available_tools.get_system_tools()

        assert isinstance(tools, dict)
        assert all(isinstance(name, str) for name in tools)
        assert all(isinstance(desc, str) for desc in tools.values())

    def test_includes_the_built_in_currentdate_tool(self, available_tools):
        tools = available_tools.get_system_tools()

        assert 'currentdate' in tools
        assert tools['currentdate'].strip()

    def test_every_description_is_non_empty(self, available_tools):
        for name, description in available_tools.get_system_tools().items():
            assert description.strip(), f'{name} has an empty description'

    def test_names_are_lowercase(self, available_tools):
        for name in available_tools.get_system_tools():
            assert name == name.lower()

    def test_returned_dict_is_a_copy(self, available_tools):
        tools = available_tools.get_system_tools()
        tools['injected'] = 'not a real tool'

        assert 'injected' not in available_tools.get_system_tools()


@pytest.mark.unit
class TestToolInstances:
    def test_get_tool_instance_returns_the_registered_tool(
        self, available_tools
    ):
        tool = available_tools.get_tool_instance('currentdate')

        assert isinstance(tool, CurrentDateTool)

    def test_get_tool_instance_is_case_insensitive(self, available_tools):
        assert available_tools.get_tool_instance('CurrentDate') is not None
        assert available_tools.get_tool_instance('CURRENTDATE') is not None

    def test_get_tool_instance_returns_none_for_unknown_name(
        self, available_tools
    ):
        assert available_tools.get_tool_instance('does_not_exist') is None

    def test_all_instances_implement_base_tool(self, available_tools):
        instances = available_tools.get_all_tool_instances()

        assert instances
        assert all(isinstance(tool, BaseTool) for tool in instances.values())

    def test_instance_keys_match_the_described_tools(self, available_tools):
        assert set(available_tools.get_all_tool_instances()) == set(
            available_tools.get_system_tools()
        )

    def test_mutating_the_returned_dict_does_not_affect_the_registry(
        self, available_tools
    ):
        instances = available_tools.get_all_tool_instances()
        instances.pop('currentdate')

        assert 'currentdate' in available_tools.get_all_tool_instances()


@pytest.mark.unit
class TestLazyLoading:
    def test_catalog_loads_optional_tool_lazily(
        self, available_tools, fake_read_local_file_tool
    ):
        tools = available_tools.get_system_tools()

        assert 'readlocalfile' in tools
        assert fake_read_local_file_tool.construction_count == 1

    def test_lazy_load_constructs_optional_tool_only_once(
        self, available_tools, fake_read_local_file_tool
    ):
        first = available_tools.get_system_tools()
        second = available_tools.get_system_tools()

        assert 'readlocalfile' in first
        assert 'readlocalfile' in second
        assert fake_read_local_file_tool.construction_count == 1
        assert available_tools.get_tool_instance('READLOCALFILE') is not None

    def test_missing_optional_dependencies_do_not_break_the_catalog(
        self, available_tools, missing_read_local_file_tool, caplog
    ):
        with caplog.at_level(logging.WARNING):
            tools = available_tools.get_system_tools()

        assert 'currentdate' in tools
        assert 'readlocalfile' not in tools
        assert any(
            'ReadLocalFileTool not available' in record.getMessage()
            for record in caplog.records
        )

    def test_unavailable_tool_is_not_offered_as_an_instance(
        self, available_tools, missing_read_local_file_tool
    ):
        available_tools.get_system_tools()

        assert available_tools.get_tool_instance('readlocalfile') is None
