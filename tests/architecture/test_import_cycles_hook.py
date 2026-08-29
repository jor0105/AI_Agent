"""Guardrails for the import-cycle pre-commit hook itself.

The hook at ``scripts/check-import-cycles.py`` is repository code that
gates every commit, so it needs the same protection as the package it
inspects. These tests exercise ``find_cycles`` directly against hand-built
graphs -- the real package is (correctly) acyclic, so it can never prove the
detector actually detects anything.
"""

import importlib.util
import pathlib
from types import ModuleType

import grimp
import pytest

HOOK_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / 'scripts'
    / 'check-import-cycles.py'
)
PACKAGE = 'createagents'


def _load_hook() -> ModuleType:
    """Import the hook by path, since it is not an installed module."""
    spec = importlib.util.spec_from_file_location('_cycle_hook', HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGraph:
    """Minimal stand-in for the slice of grimp's API the hook uses."""

    def __init__(self, adjacency: dict[str, list[str]]) -> None:
        self.modules = set(adjacency)
        self._adjacency = adjacency

    def find_modules_directly_imported_by(self, module: str) -> list[str]:
        """Return the modules imported directly by ``module``."""
        return self._adjacency[module]


@pytest.fixture(scope='module')
def hook():
    """The loaded hook module."""
    return _load_hook()


@pytest.mark.unit
class TestFindCycles:
    def test_detects_two_module_cycle(self, hook):
        graph = FakeGraph({'a': ['b'], 'b': ['a']})
        assert hook.find_cycles(graph) == [['a', 'b']]

    def test_detects_the_package_root_cycle_the_hook_exists_for(self, hook):
        # `pkg/__init__` exports a submodule that reaches back through the
        # root -- the shape the hook's docstring calls out.
        graph = FakeGraph(
            {'pkg': ['pkg.sub'], 'pkg.sub': ['pkg'], 'other': []}
        )
        assert hook.find_cycles(graph) == [['pkg', 'pkg.sub']]

    def test_detects_longer_cycle(self, hook):
        graph = FakeGraph({'a': ['b'], 'b': ['c'], 'c': ['a']})
        assert hook.find_cycles(graph) == [['a', 'b', 'c']]

    def test_detects_self_import(self, hook):
        graph = FakeGraph({'a': ['a'], 'b': []})
        assert hook.find_cycles(graph) == [['a']]

    def test_ignores_acyclic_graph(self, hook):
        # Diamond: a shared dependency is not a cycle.
        graph = FakeGraph({'a': ['b', 'c'], 'b': ['d'], 'c': ['d'], 'd': []})
        assert hook.find_cycles(graph) == []

    def test_ignores_empty_graph(self, hook):
        assert hook.find_cycles(FakeGraph({})) == []

    def test_reports_disjoint_cycles_separately(self, hook):
        graph = FakeGraph(
            {'a': ['b'], 'b': ['a'], 'x': ['y'], 'y': ['x'], 'lone': ['a']}
        )
        assert sorted(hook.find_cycles(graph)) == [['a', 'b'], ['x', 'y']]

    def test_output_is_deterministic(self, hook):
        graph = FakeGraph({'c': ['a'], 'a': ['b'], 'b': ['c']})
        assert hook.find_cycles(graph) == [['a', 'b', 'c']]

    def test_deep_chain_does_not_exhaust_the_stack(self, hook):
        # Iterative Tarjan is the whole point; recursion would die here.
        depth = 5000
        adjacency = {f'm{i}': [f'm{i + 1}'] for i in range(depth)}
        adjacency[f'm{depth}'] = []
        assert hook.find_cycles(FakeGraph(adjacency)) == []

    def test_deep_chain_that_closes_is_reported(self, hook):
        depth = 5000
        adjacency = {f'm{i}': [f'm{i + 1}'] for i in range(depth)}
        adjacency[f'm{depth}'] = ['m0']
        assert len(hook.find_cycles(FakeGraph(adjacency))) == 1


@pytest.mark.unit
class TestTypeCheckingContract:
    """The hook must judge runtime imports only.

    A ``TYPE_CHECKING`` import cannot raise the ImportError the hook exists to
    prevent, and guarding an import that way is how this package *breaks*
    cycles. Counting those edges would flag the correct design.
    """

    def test_hook_asks_grimp_to_exclude_type_checking_imports(
        self, hook, monkeypatch
    ):
        captured: dict[str, object] = {}

        def fake_build_graph(package, **kwargs):
            captured['package'] = package
            captured['kwargs'] = kwargs
            return FakeGraph({'a': []})

        monkeypatch.setattr(hook.grimp, 'build_graph', fake_build_graph)
        assert hook.main() == 0
        assert captured['package'] == PACKAGE
        assert captured['kwargs'] == {'exclude_type_checking_imports': True}

    def test_type_checking_edges_exist_and_are_excluded(self):
        # Documents the divergence the exclusion resolves: dropping these
        # edges is a real change to the graph, not a no-op.
        with_tc = grimp.build_graph(PACKAGE)
        without_tc = grimp.build_graph(
            PACKAGE, exclude_type_checking_imports=True
        )
        edges_with = {
            (m, t)
            for m in with_tc.modules
            for t in with_tc.find_modules_directly_imported_by(m)
        }
        edges_without = {
            (m, t)
            for m in without_tc.modules
            for t in without_tc.find_modules_directly_imported_by(m)
        }
        assert edges_without < edges_with

    def test_cli_protocol_edges_are_annotation_only(self):
        # The design intent this fix protects: command handlers name
        # `AgentFacade` only in annotations, which is what lets the CLI stay
        # decoupled from the facade. If one of these becomes a runtime import,
        # the decoupling is gone and this test should say so.
        without_tc = grimp.build_graph(
            PACKAGE, exclude_type_checking_imports=True
        )
        protocols = f'{PACKAGE}.presentation.cli.protocols'
        runtime_importers = {
            m
            for m in without_tc.modules
            if protocols in without_tc.find_modules_directly_imported_by(m)
        }
        assert not runtime_importers, (
            'CLI protocols must be imported under TYPE_CHECKING only; '
            f'runtime importers: {sorted(runtime_importers)}'
        )


@pytest.mark.unit
class TestRealPackage:
    def test_package_has_no_runtime_import_cycles(self, hook):
        graph = grimp.build_graph(PACKAGE, exclude_type_checking_imports=True)
        cycles = hook.find_cycles(graph)
        assert not cycles, f'Import cycles in {PACKAGE}: {cycles}'

    def test_hook_exits_zero_on_the_real_package(self, hook):
        assert hook.main() == 0
