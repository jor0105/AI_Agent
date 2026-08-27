"""Fail when the package's import graph contains a cycle.

import-linter (see [tool.importlinter] in pyproject.toml) enforces the
*layering* between top-level packages, but it has no contract type that
expresses "no cycles anywhere". The gap matters: the common Python cycle is a
submodule importing its own package root (``from ...core import x`` while
``core/__init__`` imports that same submodule). That is invisible to a layers
contract because the package root is the container, not a sibling layer.

Such a cycle usually still imports successfully -- but only because of the
statement order inside ``__init__.py``. Reordering imports turns it into an
ImportError at package import time. This hook makes the fragility explicit.

Scope: runtime imports only. ``TYPE_CHECKING``-guarded imports are excluded
because they cannot produce the ImportError described above -- the interpreter
never executes them. Including them would flag the very pattern this package
uses to *break* cycles (``presentation/cli/protocols.py`` declares protocols
that commands reference only in annotations), and the message below would then
give advice that makes the design worse. This matches the exclusion already
applied by ``tests/architecture/test_layer_dependencies.py``, so the hook and
the test enforce one contract instead of two.
"""

from __future__ import annotations

import sys

import grimp

PACKAGE = 'createagents'

# There is deliberately no allowlist here. The one cycle this package used to
# have (the CLI and the facade importing each other) was removed by giving the
# CLI its own `AgentFacade` protocol, not suppressed. Adding an exemption here
# would re-open the door this hook exists to keep shut.


def find_cycles(graph: grimp.ImportGraph) -> list[list[str]]:
    """Return every cyclic strongly connected component of the graph.

    A component is cyclic when it holds more than one module, or when it
    holds a single module that imports itself. Iterative Tarjan, so a deep
    import graph cannot blow the stack.
    """
    modules = sorted(graph.modules)
    adjacency = {
        m: sorted(graph.find_modules_directly_imported_by(m)) for m in modules
    }

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []
    counter = 0

    for root in modules:
        if root in index:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, child_i = work[-1]
            if child_i == 0:
                index[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)

            recursed = False
            children = adjacency.get(node, ())
            for i in range(child_i, len(children)):
                child = children[i]
                if child not in index:
                    work[-1] = (node, i + 1)
                    work.append((child, 0))
                    recursed = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if recursed:
                continue

            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or node in adjacency.get(node, ()):
                    cycles.append(sorted(component))

            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])

    return cycles


def main() -> int:
    graph = grimp.build_graph(PACKAGE, exclude_type_checking_imports=True)
    cycles = find_cycles(graph)

    if not cycles:
        print(f'  ok no import cycles ({len(graph.modules)} modules)')
        return 0

    print(f'Import cycle(s) detected in {PACKAGE}:', file=sys.stderr)
    for component in cycles:
        print('', file=sys.stderr)
        for module in component:
            targets = sorted(
                set(graph.find_modules_directly_imported_by(module))
                & set(component)
            )
            for target in targets:
                details = graph.get_import_details(
                    importer=module, imported=target
                )
                where = (
                    f' (line {details[0]["line_number"]})'
                    if details and details[0].get('line_number')
                    else ''
                )
                print(f'  {module} -> {target}{where}', file=sys.stderr)
    print(
        '\nImport a defining module directly instead of routing through the '
        'package root.',
        file=sys.stderr,
    )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
