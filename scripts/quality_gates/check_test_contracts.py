"""Audit complete staged or working-tree Python test snapshots."""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
from pathlib import Path

from git_index import (
    GitInspectionError,
    indexed_paths,
    normalize_path,
    read_index_text,
    repository_root,
)
from test_contract_ast import TestContractVisitor, Violation


def is_test_file(file_path: str) -> bool:
    """Return whether a repository path belongs to tests."""
    normalized = normalize_path(file_path).lower()
    if normalized.startswith(('.venv/', 'venv/', '.git/', 'site/', 'dist/')):
        return False
    return (
        normalized.startswith(('tests/', 'test/')) or '/tests/' in normalized
    ) and normalized.endswith('.py')


def audit_source(source: str, file_path: str) -> list[Violation]:
    """Audit Python source code for test contract violations."""
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as err:
        return [
            Violation(
                file_path,
                err.lineno or 1,
                'SYNTAX_ERROR',
                f'Syntax error: {err.msg}',
            )
        ]
    visitor = TestContractVisitor(file_path)
    visitor.collect_bindings(tree)
    visitor.visit(tree)
    return visitor.violations


def audit_test_files(
    root: Path,
    paths: Sequence[str] | None = None,
    from_working_tree: bool = False,
) -> list[Violation]:
    """Audit selected, working-tree, or complete staged test files."""
    if paths is not None:
        target_paths = sorted(p for p in paths if is_test_file(p))
    elif from_working_tree:
        target_paths = sorted(
            normalize_path(path.relative_to(root))
            for path in root.rglob('*.py')
            if is_test_file(str(path.relative_to(root)))
        )
    else:
        target_paths = sorted(
            p for p in indexed_paths(root) if is_test_file(p)
        )

    violations: list[Violation] = []
    for rel_path in target_paths:
        if from_working_tree:
            full_path = root / rel_path
            if not full_path.exists():
                continue
            content = full_path.read_text(encoding='utf-8')
        else:
            content = read_index_text(rel_path, root)
            if content is None:
                continue
        violations.extend(audit_source(content, rel_path))
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    """Run the test contract quality gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--working-tree',
        action='store_true',
        help='Inspect working-tree files instead of the staged Git index.',
    )
    parser.add_argument(
        'files', nargs='*', help='Optional specific test files.'
    )
    args = parser.parse_args(argv)

    try:
        root = repository_root()
        paths = args.files if args.files else None
        violations = audit_test_files(
            root=root, paths=paths, from_working_tree=args.working_tree
        )
    except (GitInspectionError, OSError, UnicodeError) as err:
        print(f'ERROR [TEST_CONTRACTS]: {err}', file=sys.stderr)
        return 2

    if violations:
        print(
            f'FAIL [TEST_CONTRACTS]: Found {len(violations)} test contract violation(s):',
            file=sys.stderr,
        )
        for violation in violations:
            print(f'  • {violation.format()}', file=sys.stderr)
        return 1
    print(
        'PASS [TEST_CONTRACTS]: All test contracts are intact and compliant.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
