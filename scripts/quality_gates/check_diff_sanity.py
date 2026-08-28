"""Fail closed on staged debug artifacts, stubs, and lint/type bypasses."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

from git_index import GitInspectionError, repository_root, staged_diff

_BREAKPOINT = 'break' + 'point'
_DEBUGGER = 'debug' + 'ger'
_RAW_PRINT = 'raw ' + 'print'

DEBUG_PATTERNS = (
    (re.compile(rf'\b{_BREAKPOINT}\(\)'), f'{_BREAKPOINT}() call'),
    (re.compile(rf'\b{_DEBUGGER};?'), f'{_DEBUGGER} statement'),
    (
        re.compile(r'\bconsole\.(?:log|debug|trace|dir)\('),
        'console debug statement',
    ),
    (re.compile(r'(?<![A-Za-z0-9_])print\('), f'{_RAW_PRINT}() call'),
)
STUB_PATTERNS = (
    (re.compile(r'throw\s+new\s+Error\(["\']TODO'), 'TODO exception'),
    (
        re.compile(r'raise\s+NotImplementedError\(["\']TODO'),
        'TODO NotImplementedError',
    ),
    (re.compile(r'pass\s*#\s*TODO', re.IGNORECASE), 'TODO pass stub'),
)
BYPASS_PATTERNS = (
    (
        re.compile(r'@ts-(?:ignore|nocheck)\b'),
        'TypeScript suppression',
    ),
    (
        re.compile(r'#\s*type:\s*ignore\b'),
        'Python type suppression',
    ),
    (
        re.compile(r'(?://|/\*)\s*eslint-disable(?:-next-line|-line)?\b'),
        'ESLint suppression',
    ),
    (
        re.compile(r'#\s*pragma:\s*no\s+cover\b', re.IGNORECASE),
        'coverage suppression',
    ),
)
NOQA_PATTERN = re.compile(r'#\s*(?:ruff:\s*)?noqa\b', re.IGNORECASE)
DEBUG_REASON = re.compile(r'allow-debug:\s*\S+.*', re.IGNORECASE)
STUB_REASON = re.compile(
    r'(?:allow-stub|stub-reason|todo-reason):\s*\S+.*', re.IGNORECASE
)
BYPASS_REASON = re.compile(
    r'\ballow-bypass:\s*\S.*',
    re.IGNORECASE,
)
NON_SOURCE_SUFFIXES = frozenset(
    {
        '.csv',
        '.gif',
        '.ico',
        '.jpeg',
        '.jpg',
        '.json',
        '.lock',
        '.map',
        '.markdown',
        '.md',
        '.png',
        '.rst',
        '.svg',
        '.toml',
        '.tsv',
        '.txt',
        '.xml',
        '.yaml',
        '.yml',
    }
)
_CENTRAL_HARNESS_PREFIX = '.agents/'


def _is_source_file(path: str) -> bool:
    """Return whether a diff path contains authored executable source."""
    return Path(path).suffix.lower() not in NON_SOURCE_SUFFIXES


def _is_central_harness_path(path: str) -> bool:
    """Return whether a path is validated by the central harness."""
    return path.replace('\\', '/').startswith(_CENTRAL_HARNESS_PREFIX)


def _normalize_path(path: str) -> str:
    """Return a repository-relative path in the diff's canonical form."""
    normalized = path.replace('\\', '/')
    while normalized.startswith('./'):
        normalized = normalized[2:]
    return normalized


def _violation(
    content: str,
    path: str,
    line: int,
    allow_print: bool,
) -> list[str]:
    """Return all policy violations present in one staged added line."""
    errors: list[str] = []
    for pattern, label in DEBUG_PATTERNS:
        if label == 'raw print() call' and allow_print:
            continue
        if pattern.search(content) and not DEBUG_REASON.search(content):
            errors.append(f'{path}:{line}: [DEBUG] {label}')
    for pattern, label in STUB_PATTERNS:
        if pattern.search(content) and not STUB_REASON.search(content):
            errors.append(f'{path}:{line}: [STUB] {label}')
    if NOQA_PATTERN.search(content):
        errors.append(f'{path}:{line}: [BYPASS] Ruff suppression is forbidden')
    for pattern, label in BYPASS_PATTERNS:
        if pattern.search(content) and not BYPASS_REASON.search(content):
            errors.append(f'{path}:{line}: [BYPASS] {label}')
    return errors


def scan_diff(diff: str, allow_print_files: Iterable[str] = ()) -> list[str]:
    """Scan added staged source lines and return actionable failures."""
    errors: list[str] = []
    allowed_print_files = {_normalize_path(path) for path in allow_print_files}
    path = ''
    line_number = 0
    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            path = line[6:]
            continue
        if line.startswith('@@ '):
            match = re.search(r'\+(\d+)', line)
            if match:
                line_number = int(match.group(1)) - 1
            continue
        if line.startswith(' '):
            line_number += 1
            continue
        if not line.startswith('+') or line.startswith('+++'):
            continue
        if _is_central_harness_path(path) or not _is_source_file(path):
            continue
        line_number += 1
        content = line[1:].strip()
        if content:
            errors.extend(
                _violation(
                    content,
                    path,
                    line_number,
                    _normalize_path(path) in allowed_print_files,
                )
            )
    return errors


def main() -> int:
    """Run the staged diff-sanity gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*')
    parser.add_argument(
        '--allow-print-file',
        action='append',
        default=[],
        metavar='PATH',
        help='Allow print() only in this exact repository-relative file.',
    )
    args = parser.parse_args()
    try:
        root = repository_root()
        diff = staged_diff(root, args.files)
    except GitInspectionError as err:
        print(f'ERROR [DIFF_SANITY]: {err}', file=sys.stderr)
        return 2
    if not diff.strip():
        print('SKIP [DIFF_SANITY]: No staged source additions to inspect.')
        return 0
    errors = scan_diff(diff, args.allow_print_file)
    if not errors:
        print('PASS [DIFF_SANITY]: No staged agent artifacts detected.')
        return 0
    print(
        'FAIL [DIFF_SANITY]: Staged agent artifacts detected:', file=sys.stderr
    )
    for error in errors:
        print(f'  • {error}', file=sys.stderr)
    print(
        'Resolution: fix the code or use a narrow, reasoned exception; '
        'Ruff suppressions are never accepted.',
        file=sys.stderr,
    )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
