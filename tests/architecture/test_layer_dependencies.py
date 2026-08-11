"""Architecture guardrails.

These tests fail when a change reintroduces a layering inversion or an import
cycle between packages. They read the import graph statically, so they never
execute the modules they inspect.
"""

import ast
import collections
import pathlib

import pytest

SRC = pathlib.Path(__file__).resolve().parents[2] / 'src'
PACKAGE = 'createagents'

# Packages each layer is allowed to import from, at module import time.
ALLOWED: dict[str, set[str]] = {
    'createagents.domain': set(),
    'createagents.application': {'createagents.domain'},
    'createagents.utils': set(),
    'createagents.infra': {
        'createagents.domain',
        'createagents.application',
        'createagents.utils',
    },
    'createagents.presentation': {
        'createagents.domain',
        'createagents.application',
        'createagents.infra',
        'createagents.utils',
    },
    'createagents.main': {
        'createagents.domain',
        'createagents.application',
        'createagents.infra',
        'createagents.presentation',
        'createagents.utils',
    },
    PACKAGE: {
        'createagents.domain',
        'createagents.application',
        'createagents.infra',
        'createagents.main',
        'createagents.presentation',
        'createagents.utils',
    },
}


def _modules() -> dict[str, pathlib.Path]:
    modules = {}
    for path in SRC.rglob('*.py'):
        if '__pycache__' in str(path):
            continue
        name = str(path.relative_to(SRC)).replace('/', '.')[: -len('.py')]
        if name.endswith('.__init__'):
            name = name[: -len('.__init__')]
        modules[name] = path
    return modules


def _resolve(module: str, node: ast.ImportFrom, is_package: bool) -> str:
    if not node.level:
        return node.module or ''
    parts = module.split('.')
    base = parts if is_package else parts[:-1]
    up = node.level - 1
    if up:
        base = base[: len(base) - up]
    return '.'.join(base + ([node.module] if node.module else []))


def _top_level_graph() -> dict[str, set[str]]:
    """Map each module to the modules it imports at import time."""
    modules = _modules()
    graph: dict[str, set[str]] = collections.defaultdict(set)

    for module, path in modules.items():
        is_package = path.name == '__init__.py'
        tree = ast.parse(path.read_text())

        class Visitor(ast.NodeVisitor):
            """Collects imports that run when the module is imported."""

            def __init__(self, module: str, is_package: bool) -> None:
                self.module = module
                self.is_package = is_package
                self.depth = 0
                self.type_checking = 0

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                """Skip imports deferred inside a function body."""
                self.depth += 1
                self.generic_visit(node)
                self.depth -= 1

            # Sync and async function bodies use the same import traversal.
            visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

            def visit_If(self, node: ast.If) -> None:
                """Skip imports guarded by TYPE_CHECKING."""
                guarded = 'TYPE_CHECKING' in ast.unparse(node.test)
                self.type_checking += guarded
                self.generic_visit(node)
                self.type_checking -= guarded

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                """Record a runtime import edge."""
                if self.depth or self.type_checking:
                    return
                target = _resolve(self.module, node, self.is_package)
                if not target.startswith(PACKAGE):
                    return
                candidates = {target} | {
                    f'{target}.{alias.name}' for alias in node.names
                }
                hits = {name for name in candidates if name in modules}
                graph[self.module].update(hits or ({target} & modules.keys()))

        Visitor(module, is_package).visit(tree)

    return graph


def _package_of(module: str) -> str:
    parts = module.split('.')
    return '.'.join(parts[:2]) if len(parts) > 1 else module


@pytest.mark.unit
class TestLayerDependencies:
    def test_no_package_level_import_cycles(self):
        graph = _top_level_graph()
        packages: dict[str, set[str]] = collections.defaultdict(set)
        for source, targets in graph.items():
            for target in targets:
                if _package_of(source) != _package_of(target):
                    packages[_package_of(source)].add(_package_of(target))

        cycles = [
            (a, b)
            for a, deps in packages.items()
            for b in deps
            if a in packages.get(b, set()) and a < b
        ]
        assert not cycles, f'Import cycles between packages: {cycles}'

    def test_layers_only_import_allowed_packages(self):
        graph = _top_level_graph()
        violations = []
        for source, targets in graph.items():
            source_pkg = _package_of(source)
            allowed = ALLOWED.get(source_pkg)
            if allowed is None:
                continue
            for target in targets:
                target_pkg = _package_of(target)
                if target_pkg == source_pkg or target_pkg in allowed:
                    continue
                violations.append(f'{source} -> {target}')
        assert not violations, (
            'Layer violations (see ALLOWED in this file): '
            + ', '.join(sorted(violations))
        )

    def test_application_never_imports_infra_or_main(self):
        graph = _top_level_graph()
        offenders = [
            f'{source} -> {target}'
            for source, targets in graph.items()
            if source.startswith('createagents.application')
            for target in targets
            if target.startswith(('createagents.infra', 'createagents.main'))
        ]
        assert not offenders, (
            'The application layer must depend only on the domain; '
            f'declare a port instead. Offenders: {offenders}'
        )
