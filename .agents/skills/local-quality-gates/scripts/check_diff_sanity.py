#!/usr/bin/env python3
"""Portable sanity checker for git diffs to detect AI coding agent traps.

Detects common issues introduced on added/modified lines (+):
  - Leftover debug statements (console.log, breakpoint, debugger, raw print)
  - Stubbed implementations / unfulfilled placeholders (TODO throws, pass stubs)
  - Newly added type/lint bypasses (@ts-ignore, type: ignore, noqa)

The inline noqa form is always rejected; no allow annotation can override
that rule.

Fail-closed: Exits with code 2 on git errors, code 1 on violations, code 0 on clean pass.
Zero external dependencies (Python 3.10+ standard library only).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


class GitInspectionError(Exception):
    """Raised when git diff cannot be inspected."""


DEBUG_PATTERNS = [
    (re.compile(r'\bbreakpoint\(\)'), 'breakpoint() call detected'),
    (re.compile(r'\bdebugger;?'), 'debugger statement detected'),
    (
        re.compile(r'\bconsole\.(?:log|debug|trace|dir)\('),
        'console.log/debug statement detected',
    ),
    (
        re.compile(r'(?<![a-zA-Z0-9_])print\('),
        'raw print() call detected (use logger or allow in CLI files)',
    ),
]

STUB_PATTERNS = [
    (
        re.compile(r'throw\s+new\s+Error\(["\']TODO'),
        'TODO placeholder exception thrown',
    ),
    (
        re.compile(r'raise\s+NotImplementedError\(["\']TODO'),
        'TODO NotImplementedError thrown',
    ),
    (
        re.compile(r'pass\s*#\s*TODO', re.IGNORECASE),
        'pass TODO placeholder detected',
    ),
]

BYPASS_PATTERNS = [
    (
        re.compile(r'@ts-(?:ignore|nocheck)\b'),
        'TypeScript check bypass (@ts-ignore/@ts-nocheck) added',
    ),
    (
        re.compile(r'#\s*type:\s*ignore\b'),
        'Python type check bypass (# type: ignore) added',
    ),
    (
        re.compile(r'(?://|/\*)\s*eslint-disable(?:-next-line|-line)?\b'),
        'ESLint bypass comment added',
    ),
]

# Category-specific allow comments (require explicit reason content)
DEBUG_ALLOW_RE = re.compile(r'allow-debug:\s*\S+.*', re.IGNORECASE)
STUB_ALLOW_RE = re.compile(
    r'(?:allow-stub|stub-reason|todo-reason):\s*\S+.*', re.IGNORECASE
)
BYPASS_ALLOW_RE = re.compile(
    r'(?:allow-bypass|--\s*reason:|#\s*reason:)\s*\S+.*',
    re.IGNORECASE,
)
NOQA_PATTERN = re.compile(r'#\s*noqa\b', re.IGNORECASE)
NOQA_LABEL = '# ' + 'noqa'
NOQA_DESCRIPTION = f'Linter bypass ({NOQA_LABEL}) is never permitted'

NON_INSPECTABLE_EXTENSIONS = frozenset(
    {
        '.md',
        '.markdown',
        '.rst',
        '.txt',
        '.json',
        '.yaml',
        '.yml',
        '.toml',
        '.lock',
        '.csv',
        '.tsv',
        '.xml',
        '.svg',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.ico',
        '.map',
    }
)


def is_inspectable_file(file_path: str) -> bool:
    """Determine if a file is an authored source/script file to be checked."""
    p = Path(file_path)
    return p.suffix.lower() not in NON_INSPECTABLE_EXTENSIONS


def get_staged_diff(target_files: list[str] | None = None) -> str:
    """Retrieve staged git diff for specified files or all staged changes."""
    cmd = ['git', 'diff', '--cached', '--no-color', '-U0', '--']
    if target_files:
        cmd.extend(target_files)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout
    except (
        subprocess.CalledProcessError,
        subprocess.SubprocessError,
        FileNotFoundError,
    ) as err:
        raise GitInspectionError(str(err)) from err


def is_cli_or_script_file(file_path: str) -> bool:
    """Determine if file is a CLI entry point or script where print is expected."""
    p = Path(file_path)
    posix_path = p.as_posix().lower()
    return (
        '/cli/' in posix_path
        or '/scripts/' in posix_path
        or posix_path.startswith('scripts/')
        or p.name in ('manage.py', 'cli.py', 'main.py')
    )


def _check_debug_violations(
    content: str,
    file_path: str,
    line_num: int,
    allow_debug_in_scripts: bool,
    allow_print_files: frozenset[str],
) -> list[str]:
    errors: list[str] = []
    is_script = is_cli_or_script_file(file_path)
    allow_print = allow_debug_in_scripts and is_script
    allow_print = allow_print or file_path in allow_print_files
    for pattern, desc in DEBUG_PATTERNS:
        if 'print(' in desc and allow_print:
            continue
        if pattern.search(content) and not DEBUG_ALLOW_RE.search(content):
            errors.append(f'{file_path}:{line_num}: [DEBUG] {desc}')
    return errors


def _check_stub_violations(
    content: str, file_path: str, line_num: int
) -> list[str]:
    errors: list[str] = []
    for pattern, desc in STUB_PATTERNS:
        if pattern.search(content) and not STUB_ALLOW_RE.search(content):
            errors.append(f'{file_path}:{line_num}: [STUB] {desc}')
    return errors


def _check_bypass_violations(
    content: str, file_path: str, line_num: int
) -> list[str]:
    errors: list[str] = []
    for pattern, desc in BYPASS_PATTERNS:
        if pattern.search(content) and not BYPASS_ALLOW_RE.search(content):
            errors.append(f'{file_path}:{line_num}: [BYPASS] {desc}')
    return errors


def _check_noqa_violations(
    content: str, file_path: str, line_num: int
) -> list[str]:
    """Reject inline noqa independently of the other bypass policies."""
    if not NOQA_PATTERN.search(content):
        return []
    return [
        f'{file_path}:{line_num}: [BYPASS] {NOQA_DESCRIPTION}',
    ]


def scan_diff(
    diff_text: str,
    allow_debug_in_scripts: bool = True,
    check_bypasses: bool = True,
    allow_print_files: frozenset[str] | set[str] | None = None,
) -> list[str]:
    """Scan added diff lines for violations and return formatted error messages."""
    errors: list[str] = []
    current_file = ''
    line_num = 0
    allowed_print_files = frozenset(allow_print_files or ())

    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            current_file = line[6:]
            continue
        if line.startswith('@@ '):
            m = re.search(r'\+(\d+)', line)
            if m:
                line_num = int(m.group(1)) - 1
            continue

        if not line.startswith('+') or line.startswith('+++'):
            continue

        if not is_inspectable_file(current_file):
            continue

        line_num += 1
        added_content = line[1:].strip()
        if not added_content:
            continue

        errors.extend(
            _check_debug_violations(
                added_content,
                current_file,
                line_num,
                allow_debug_in_scripts,
                allowed_print_files,
            )
        )
        errors.extend(
            _check_stub_violations(added_content, current_file, line_num)
        )
        errors.extend(
            _check_noqa_violations(added_content, current_file, line_num)
        )
        if check_bypasses:
            errors.extend(
                _check_bypass_violations(added_content, current_file, line_num)
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'files',
        nargs='*',
        help='Specific files to check. If omitted, checks all staged files.',
    )
    parser.add_argument(
        '--disallow-script-prints',
        action='store_true',
        help='Fail on print() even inside scripts/ or cli/ directories.',
    )
    parser.add_argument(
        '--allow-print-file',
        action='append',
        default=[],
        metavar='PATH',
        help=(
            'Allow print() in this explicitly configured CLI path; repeat '
            'for each path.'
        ),
    )
    args = parser.parse_args()

    try:
        diff_text = get_staged_diff(args.files if args.files else None)
    except GitInspectionError as err:
        sys.stderr.write(
            f'ERROR [DIFF_SANITY]: unable to inspect staged Git changes: {err}\n'
        )
        return 2

    if not diff_text.strip():
        sys.stdout.write(
            'SKIP [DIFF_SANITY]: No staged diff additions to inspect.\n'
        )
        return 0

    errors = scan_diff(
        diff_text,
        allow_debug_in_scripts=not args.disallow_script_prints,
        check_bypasses=True,
        allow_print_files=frozenset(
            Path(path).as_posix() for path in args.allow_print_file
        ),
    )

    if errors:
        sys.stderr.write(
            'FAIL [DIFF_SANITY]: Potential AI agent artifacts detected in staged diff:\n'
        )
        for error_msg in errors:
            sys.stderr.write(f'  • {error_msg}\n')
        sys.stderr.write(
            '\nResolution: Fix the code, use the appropriate file/scope, or '
            'configure the lint rule explicitly for that file. '
            f'{NOQA_LABEL} is never permitted; other annotations require a '
            'specific reason '
            '("allow-debug", "allow-stub", or "-- reason: <why>").\n'
        )
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
