"""AST rules for the staged test-contract quality gate."""

from __future__ import annotations

import ast
import operator
import re
from collections.abc import Container, Iterator
from dataclasses import dataclass

_MANGLED_ATTRIBUTE_RE = re.compile(r'^_[A-Za-z0-9_]+__[A-Za-z0-9_]+$')
_MANGLED_TARGET_RE = re.compile(
    r'(?<![A-Za-z0-9_])_[A-Za-z0-9_]+__[A-Za-z0-9_]+(?![A-Za-z0-9_])'
)
_BUILTIN_ACCESS_NAMES = frozenset({'getattr', 'setattr', 'delattr'})
_TEST_EVIDENCE_NAMES = frozenset(
    {
        'catch_warnings',
        'deprecated_call',
        'fail',
        'raises',
        'skip',
        'warns',
        'xfail',
    }
)


def _contains(left: object, right: object) -> bool:
    """Return whether the right literal container contains the left value."""
    if not isinstance(right, Container):
        raise TypeError('right-hand comparison value is not a container')
    return operator.contains(right, left)


def _not_contains(left: object, right: object) -> bool:
    """Return whether the right literal container does not contain the left."""
    return not _contains(left, right)


_COMPARISON_OPERATORS = {
    ast.Eq: operator.eq,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: _contains,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.NotEq: operator.ne,
    ast.NotIn: _not_contains,
}


@dataclass(frozen=True)
class Violation:
    """A single test contract violation."""

    file_path: str
    line: int
    category: str
    message: str

    def format(self) -> str:
        """Format the violation as a readable string."""
        return (
            f'{self.file_path}:{self.line}: [{self.category}] {self.message}'
        )


def _dotted_name(node: ast.AST) -> str | None:
    """Return a dotted name for a simple name or attribute expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent is not None:
            return f'{parent}.{node.attr}'
    return None


def _target_names(node: ast.AST) -> Iterator[str]:
    """Yield names assigned by a simple, destructuring target."""
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, (ast.List, ast.Tuple)):
        for element in node.elts:
            yield from _target_names(element)


def _literal_string(
    node: ast.AST, constants: dict[str, str] | None = None
) -> str | None:
    """Resolve a literal string or a known module-level string constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if constants is not None and isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def _is_mangled_attribute(name: str) -> bool:
    """Return whether an attribute is private or name-mangled."""
    return bool(_MANGLED_ATTRIBUTE_RE.fullmatch(name)) or (
        name.startswith('__') and not name.endswith('__')
    )


def _boolean_truth(node: ast.BoolOp) -> bool | None:
    """Evaluate a constant boolean expression when its outcome is obvious."""
    results = [_constant_truth(value) for value in node.values]
    if isinstance(node.op, ast.Or):
        if any(result is True for result in results):
            return True
        return False if all(result is not None for result in results) else None
    if any(result is False for result in results):
        return False
    return True if all(result is not None for result in results) else None


def _comparison_truth(node: ast.Compare) -> bool | None:
    """Evaluate a comparison made entirely from supported literals."""
    values = [node.left, *node.comparators]
    try:
        literal_values = [ast.literal_eval(value) for value in values]
        result = True
        for index, operation in enumerate(node.ops):
            compare = _COMPARISON_OPERATORS.get(type(operation))
            if compare is None:
                return None
            result = result and compare(
                literal_values[index], literal_values[index + 1]
            )
        return bool(result)
    except (TypeError, ValueError, SyntaxError):
        return None


def _constant_truth(node: ast.AST) -> bool | None:
    """Evaluate obvious constant assertion outcomes without executing code."""
    if isinstance(node, ast.Constant):
        return bool(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        result = _constant_truth(node.operand)
        return None if result is None else not result
    if isinstance(node, ast.BoolOp):
        return _boolean_truth(node)
    if isinstance(node, ast.Compare):
        return _comparison_truth(node)
    return None


def _assignment_parts(
    node: ast.AST,
) -> tuple[list[ast.expr], ast.expr] | None:
    """Return assignment targets and value for supported assignment nodes."""
    if isinstance(node, ast.Assign):
        return node.targets, node.value
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return [node.target], node.value
    return None


class TestContractVisitor(ast.NodeVisitor):
    """AST visitor that checks for test contract violations."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.violations: list[Violation] = []
        self._current_scope: list[str] = ['module']
        self._hasattr_names = {'hasattr'}
        self._builtin_names = {'builtins'}
        self._dynamic_access_names = set(_BUILTIN_ACCESS_NAMES)
        self._patch_names = {'patch'}
        self._factory_names = {'ChatAdapterFactory'}
        self._string_constants: dict[str, str] = {}

    def collect_bindings(self, tree: ast.Module) -> None:
        """Collect aliases and module constants before semantic traversal."""
        self._collect_import_bindings(tree)
        self._collect_string_constants(tree)
        self._collect_factory_aliases(tree)

    def _collect_import_bindings(self, tree: ast.Module) -> None:
        """Collect aliases imported from supported modules and symbols."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._collect_import_alias(alias)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    self._collect_from_import_alias(module, alias)

    def _collect_import_alias(self, alias: ast.alias) -> None:
        """Record one alias from a regular import statement."""
        local_name = alias.asname or alias.name.split('.')[0]
        if alias.name == 'builtins':
            self._builtin_names.add(local_name)
        if alias.name.endswith('.ChatAdapterFactory'):
            self._factory_names.add(local_name)
        if alias.name.endswith('.patch'):
            self._patch_names.add(local_name)

    def _collect_from_import_alias(
        self, module: str, alias: ast.alias
    ) -> None:
        """Record one alias from a from-import statement."""
        local_name = alias.asname or alias.name
        if module == 'builtins':
            self._collect_builtin_alias(alias.name, local_name)
        if alias.name == 'patch' and module in {'mock', 'unittest.mock'}:
            self._patch_names.add(local_name)
        if alias.name == 'ChatAdapterFactory':
            self._factory_names.add(local_name)

    def _collect_builtin_alias(self, imported: str, local_name: str) -> None:
        """Record a supported aliased built-in access function."""
        if imported == 'hasattr':
            self._hasattr_names.add(local_name)
        if imported in _BUILTIN_ACCESS_NAMES:
            self._dynamic_access_names.add(local_name)

    def _collect_string_constants(self, tree: ast.Module) -> None:
        """Collect module-level string constants used as dynamic targets."""
        for statement in tree.body:
            assignment = _assignment_parts(statement)
            if assignment is None:
                continue
            targets, expression = assignment
            value = _literal_string(expression)
            if value is None:
                continue
            for target in targets:
                for name in _target_names(target):
                    self._string_constants[name] = value

    def _collect_factory_aliases(self, tree: ast.Module) -> None:
        """Resolve transitive aliases of ChatAdapterFactory assignments."""
        for _ in range(len(tree.body) + 1):
            if not self._collect_factory_alias_pass(tree):
                break

    def _collect_factory_alias_pass(self, tree: ast.Module) -> bool:
        """Resolve one pass of factory aliases and report whether it grew."""
        changed = False
        for node in ast.walk(tree):
            assignment = _assignment_parts(node)
            if assignment is None:
                continue
            targets, value = assignment
            if not self._resolves_factory(value):
                continue
            for target in targets:
                for name in _target_names(target):
                    if name not in self._factory_names:
                        self._factory_names.add(name)
                        changed = True
        return changed

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._current_scope.append('class')
        self.generic_visit(node)
        self._current_scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._current_scope[-1] in {'module', 'class'}:
            self._check_test_function(node)
        self._current_scope.append('function')
        self.generic_visit(node)
        self._current_scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if self._current_scope[-1] in {'module', 'class'}:
            self._check_test_function(node)
        self._current_scope.append('function')
        self.generic_visit(node)
        self._current_scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_builtin_call(node.func, self._hasattr_names, 'hasattr'):
            self._add(
                node,
                'HASATTR_PROHIBITED',
                'hasattr() is prohibited in tests. Test public behavior instead.',
            )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == 'clear_cache'
            and self._resolves_factory(node.func.value)
        ):
            self._add(
                node,
                'RETIRED_FACTORY_CACHE',
                'ChatAdapterFactory.clear_cache() is retired and must not be called in tests.',
            )
        self._check_dynamic_attribute_target(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if _is_mangled_attribute(node.attr):
            self._add(
                node,
                'NAME_MANGLING_PROHIBITED',
                f"Name-mangled attribute access '{node.attr}' is prohibited in tests. Test public behavior instead.",
            )
        self.generic_visit(node)

    def visit_Pass(self, node: ast.Pass) -> None:
        self._add(
            node,
            'PASS_PROHIBITED',
            'pass statement is prohibited in test code. Use an assertion or explicit pytest outcome.',
        )

    def visit_Assert(self, node: ast.Assert) -> None:
        result = _constant_truth(node.test)
        if result is not None:
            outcome = 'truthy' if result else 'falsy'
            self._add(
                node,
                'TAUTOLOGICAL_ASSERTION',
                f'Assertion has a constant {outcome} outcome and cannot test behavior.',
            )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            if handler.body and all(
                self._is_noop_exception_statement(statement)
                for statement in handler.body
            ):
                self._add(
                    handler,
                    'SILENT_EXCEPTION_SWALLOW',
                    'Exception handler silently swallows exceptions. Use pytest.raises() or contextlib.suppress().',
                )
        self.generic_visit(node)

    def _add(self, node: ast.AST, category: str, message: str) -> None:
        self.violations.append(
            Violation(
                self.file_path,
                getattr(node, 'lineno', 1),
                category,
                message,
            )
        )

    def _is_builtin_call(
        self, function: ast.AST, names: set[str], expected_name: str
    ) -> bool:
        if isinstance(function, ast.Name):
            return function.id in names
        return (
            isinstance(function, ast.Attribute)
            and function.attr == expected_name
            and _dotted_name(function.value) in self._builtin_names
        )

    def _is_patch_call(self, function: ast.AST, object_method: bool) -> bool:
        dotted = _dotted_name(function)
        if dotted is None:
            return False
        if object_method:
            if (
                not isinstance(function, ast.Attribute)
                or function.attr != 'object'
            ):
                return False
            parent = _dotted_name(function.value)
            return parent in self._patch_names or (
                parent is not None and parent.endswith('.patch')
            )
        return dotted in self._patch_names or dotted.endswith('.patch')

    def _check_dynamic_attribute_target(self, node: ast.Call) -> None:
        access_index = None
        if any(
            self._is_builtin_call(node.func, {name}, name)
            for name in self._dynamic_access_names
        ) or self._is_patch_call(node.func, object_method=True):
            access_index = 1
        elif self._is_patch_call(node.func, object_method=False):
            access_index = 0
        if access_index is None or len(node.args) <= access_index:
            return
        target = _literal_string(
            node.args[access_index], self._string_constants
        )
        if target is not None and _MANGLED_TARGET_RE.search(target):
            self._add(
                node.args[access_index],
                'DYNAMIC_NAME_MANGLING_PROHIBITED',
                f"Dynamic attribute target '{target}' is name-mangled; test public behavior instead.",
            )

    def _resolves_factory(self, node: ast.AST) -> bool:
        dotted = _dotted_name(node)
        if dotted is None:
            return False
        return dotted in self._factory_names or (
            dotted.rsplit('.', 1)[-1] in self._factory_names
        )

    def _check_test_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        if not node.name.startswith('test_'):
            return
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                return
            if isinstance(child, ast.Call) and self._is_test_evidence_call(
                child.func
            ):
                return
        self._add(
            node,
            'EMPTY_TEST_BODY',
            f"Test function '{node.name}' has no effective assertion, warning context, or explicit pytest outcome.",
        )

    @staticmethod
    def _is_test_evidence_call(function: ast.AST) -> bool:
        if isinstance(function, ast.Name):
            return function.id in _TEST_EVIDENCE_NAMES
        return isinstance(function, ast.Attribute) and (
            function.attr.startswith('assert')
            or function.attr in _TEST_EVIDENCE_NAMES
        )

    @staticmethod
    def _is_noop_exception_statement(statement: ast.stmt) -> bool:
        return isinstance(statement, ast.Pass) or (
            isinstance(statement, ast.Return)
            and (
                statement.value is None
                or (
                    isinstance(statement.value, ast.Constant)
                    and statement.value.value is None
                )
            )
        )
