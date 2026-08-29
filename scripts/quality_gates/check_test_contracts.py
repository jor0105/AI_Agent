"""Audit complete staged or revision Python test snapshots."""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
from pathlib import Path

from git_changes import (
    GitInspectionError,
    indexed_paths,
    is_external_path,
    normalize_path,
    read_text,
    repository_root,
    revision_paths,
    verify_revision,
)
from test_contract_ast import TestContractVisitor, Violation


def is_test_file(file_path: str) -> bool:
    """Return whether a repository path belongs to tests."""
    normalized = normalize_path(file_path).lower()
    if is_external_path(normalized):
        return False
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
    revision: str | None = None,
) -> list[Violation]:
    """Audit selected or complete test files from one Git snapshot."""
    if paths is not None:
        target_paths = sorted(
            normalize_path(path) for path in paths if is_test_file(path)
        )
    else:
        if revision is None:
            target_paths = sorted(
                p for p in indexed_paths(root) if is_test_file(p)
            )
        else:
            resolved = verify_revision(revision, root)
            target_paths = sorted(
                p for p in revision_paths(root, resolved) if is_test_file(p)
            )

    violations: list[Violation] = []
    for rel_path in target_paths:
        content = (
            read_text(rel_path, root)
            if revision is None
            else read_text(rel_path, root, revision)
        )
        if content is None:
            continue
        violations.extend(audit_source(content, rel_path))
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    """Run the test contract quality gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', metavar='REV')
    parser.add_argument(
        'files', nargs='*', help='Optional specific test files.'
    )
    args = parser.parse_args(argv)

    try:
        root = repository_root()
        paths = args.files if args.files else None
        violations = audit_test_files(
            root=root, paths=paths, revision=args.revision
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
