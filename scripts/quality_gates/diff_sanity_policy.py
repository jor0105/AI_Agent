"""Pure policy checks for additions in a Git unified diff."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from git_changes import is_external_path, normalize_path


def _join(*parts: str) -> str:
    """Build policy fixtures without putting active tokens in this source."""
    return ''.join(parts)


_BREAKPOINT = _join('break', 'point')
_PDB_TRACE = _join('pdb', '.', 'set', '_trace')
_DEBUGGER = _join('debug', 'ger')
_TODO = _join('TO', 'DO')
_NOT_IMPLEMENTED = _join('Not', 'Implemented', 'Error')
_NOQA = _join('no', 'qa')
_TYPE = _join('type')
_IGNORE = _join('ignore')
_DISABLE = _join('disable')
_NO_COVER = _join('no', r'\s+', 'cover')
_NO_VERIFY = _join('--', 'no-verify')
_SKIP_ASSIGNMENT = _join('SKIP', '=')
_CONTINUE_ON_ERROR = _join('continue', '-on-error')
_SET_PLUS_E = _join('set', r'\s+', r'\+', 'e')
_ALLOW_DEBUG = _join('allow', '-', 'debug')
_ALLOW_STUB = _join('allow', '-', 'stub')
_ALLOW_BYPASS = _join('allow', '-', 'bypass')
_STUB_REASON = _join('stub', '-', 'reason')
_TODO_REASON = _join('todo', '-', 'reason')
_PRINT_CALL = _join('print', '() call')
_FLAKE8_NOQA = _join('flake', '8')
_PYLINT_DISABLE = _join('pylint', ':', ' disable')
_MYPY_IGNORE = _join('mypy', ':', ' ignore-errors')
_PYRIGHT_IGNORE = _join('pyright', ':', ' ignore')

DOCUMENTATION_SUFFIXES = frozenset({'.md', '.markdown', '.rst', '.txt'})
CODE_SUFFIXES = frozenset(
    {
        '.bash',
        '.cjs',
        '.js',
        '.jsx',
        '.mjs',
        '.py',
        '.pyi',
        '.pyw',
        '.sh',
        '.ts',
        '.tsx',
    }
)
TEXT_SUFFIXES = CODE_SUFFIXES | frozenset(
    {
        '.cfg',
        '.conf',
        '.csv',
        '.ini',
        '.json',
        '.lock',
        '.toml',
        '.tsv',
        '.xml',
        '.yaml',
        '.yml',
    }
)

DEBUG_PATTERNS = (
    (re.compile(rf'\b{_BREAKPOINT}\s*\('), f'{_BREAKPOINT}() call'),
    (re.compile(rf'\b{_PDB_TRACE}\s*\('), f'{_PDB_TRACE}() call'),
    (re.compile(rf'\b{_DEBUGGER}\b\s*;?'), f'{_DEBUGGER} statement'),
    (
        re.compile(r'\bconsole\.(?:log|debug|trace|dir)\s*\('),
        'console debug statement',
    ),
    (re.compile(r'(?<![A-Za-z0-9_])print\s*\('), _PRINT_CALL),
)
STUB_PATTERNS = (
    (
        re.compile(
            rf'(?:\b{_TODO}\b[^\n]*\b{_NOT_IMPLEMENTED}\b|'
            rf'\b{_NOT_IMPLEMENTED}\b[^\n]*\b{_TODO}\b)',
            re.I,
        ),
        f'{_TODO} {_NOT_IMPLEMENTED}',
    ),
    (
        re.compile(rf'pass\s*#\s*{_TODO}', re.I),
        f'{_TODO} pass stub',
    ),
    (
        re.compile(
            rf'\bthrow\s+(?:new\s+)?Error\s*\([^\n]*\b{_TODO}\b',
            re.I,
        ),
        f'{_TODO} JavaScript error',
    ),
)
SUPPRESSION_PATTERNS = (
    (
        re.compile(r'#\s*(?:ruff:\s*)?' + _NOQA + r'\b', re.I),
        'Ruff suppression',
    ),
    (
        re.compile(r'#\s*' + _FLAKE8_NOQA + r'\s*:\s*' + _NOQA + r'\b', re.I),
        'blanket linter suppression',
    ),
    (
        re.compile(r'#\s*' + _PYLINT_DISABLE + r'\b', re.I),
        'blanket linter suppression',
    ),
    (
        re.compile(r'#\s*' + _MYPY_IGNORE + r'\b', re.I),
        'blanket type suppression',
    ),
    (
        re.compile(r'#\s*' + _PYRIGHT_IGNORE + r'\b', re.I),
        'blanket type suppression',
    ),
    (
        re.compile(r'#\s*' + _TYPE + r'\s*:\s*' + _IGNORE + r'\b', re.I),
        'Python type suppression',
    ),
    (
        re.compile(r'@ts-(?:ignore|nocheck|expect-error)\b', re.I),
        'TypeScript suppression',
    ),
    (
        re.compile(r'(?://|/\*)\s*eslint-' + _DISABLE + r'[^\s]*\b', re.I),
        'ESLint suppression',
    ),
    (
        re.compile(r'#\s*pragma:\s*' + _NO_COVER, re.I),
        'coverage suppression',
    ),
    (
        re.compile(r'(?://|/\*)\s*(?:istanbul|c8)\s+ignore(?:\s|\*/|$)', re.I),
        'coverage suppression',
    ),
    (
        re.compile(
            r'\b(?:'
            + '|'.join(
                (
                    _ALLOW_DEBUG,
                    _ALLOW_STUB,
                    _STUB_REASON,
                    _TODO_REASON,
                    _ALLOW_BYPASS,
                )
            )
            + r')\b',
            re.I,
        ),
        'bypass marker',
    ),
)
OPERATIONAL_PATTERNS = (
    (
        re.compile(r'\b(?:curl|wget)\b[^\r\n|]*\|\s*(?:ba)?sh\b', re.I),
        'download-to-shell pipeline',
    ),
    (re.compile(re.escape(_NO_VERIFY), re.I), 'pre-commit bypass flag'),
    (re.compile(re.escape(_SKIP_ASSIGNMENT), re.I), 'hook-skip assignment'),
    (
        re.compile(re.escape(_CONTINUE_ON_ERROR) + r'\s*:\s*true\b', re.I),
        'continue-on-error configuration',
    ),
    (re.compile(r'\|\|\s*true\b', re.I), 'forced-success fallback'),
    (re.compile(_SET_PLUS_E, re.I), 'disabled shell error handling'),
)


def _is_documentation(path: str) -> bool:
    return Path(path).suffix.lower() in DOCUMENTATION_SUFFIXES


def _is_code(path: str) -> bool:
    return Path(path).suffix.lower() in CODE_SUFFIXES


def _is_text(path: str) -> bool:
    return Path(path).suffix.lower() in TEXT_SUFFIXES or not Path(path).suffix


def validate_print_allowlist(
    paths: Iterable[str], available_paths: Iterable[str]
) -> list[str]:
    """Validate repeated print exceptions against one Git tree."""
    available = {normalize_path(path) for path in available_paths}
    errors: list[str] = []
    for raw_path in paths:
        try:
            normalized = normalize_path(raw_path)
        except ValueError as error:
            errors.append(
                f'[BYPASS] invalid print allowlist path {raw_path!r}: {error}'
            )
            continue
        if any(character in normalized for character in '*?[]{}'):
            errors.append(
                f'[BYPASS] print allowlist requires an exact file: {raw_path!r}'
            )
        elif is_external_path(normalized):
            errors.append(
                f'[BYPASS] print allowlist cannot target an external path: '
                f'{normalized}'
            )
        elif normalized not in available:
            errors.append(
                f'[BYPASS] print allowlist path is not an indexed repository '
                f'file: {normalized}'
            )
    return errors


def _header_path(
    line: str, marker: str, expected_prefix: str
) -> tuple[str | None, str | None]:
    if not line.startswith(marker):
        return None, f'[ERROR] malformed diff header: {line!r}'
    value = line[len(marker) :].split('\t', 1)[0]
    if value == '/dev/null':
        return None, None
    if not value.startswith(expected_prefix):
        return None, f'[ERROR] malformed diff path: {value!r}'
    try:
        return normalize_path(value[len(expected_prefix) :]), None
    except ValueError as error:
        return None, f'[ERROR] unsafe diff path {value!r}: {error}'


def _matches(
    patterns: Sequence[tuple[re.Pattern[str], str]],
    content: str,
    path: str,
    line_number: int,
    category: str,
) -> list[str]:
    return [
        f'{path}:{line_number}: [{category}] {label}'
        for pattern, label in patterns
        if pattern.search(content)
    ]


def _line_errors(
    content: str,
    path: str,
    line_number: int,
    allowed_print_files: set[str],
) -> list[str]:
    errors = _matches(
        OPERATIONAL_PATTERNS, content, path, line_number, 'OPERATIONAL'
    )
    if _is_code(path):
        debug_errors = _matches(
            DEBUG_PATTERNS, content, path, line_number, 'DEBUG'
        )
        if path in allowed_print_files:
            debug_errors = [
                error for error in debug_errors if _PRINT_CALL not in error
            ]
        errors.extend(debug_errors)
        errors.extend(
            _matches(STUB_PATTERNS, content, path, line_number, 'STUB')
        )
    if _is_text(path) and not _is_documentation(path):
        errors.extend(
            _matches(
                SUPPRESSION_PATTERNS, content, path, line_number, 'BYPASS'
            )
        )
    return errors


@dataclass
class _DiffState:
    old_path: str | None = None
    new_path: str | None = None
    line_number: int = 0


def _scan_diff_line(
    line: str, state: _DiffState, allowed: set[str]
) -> list[str]:
    if line.startswith('--- '):
        state.old_path, error = _header_path(line, '--- ', 'a/')
        state.new_path = None
        return [error] if error else []
    if line.startswith('+++ '):
        state.new_path, error = _header_path(line, '+++ ', 'b/')
        state.line_number = 0
        return [error] if error else []
    if line.startswith('@@ '):
        match = re.search(r'\+(\d+)', line)
        state.line_number = int(match.group(1)) - 1 if match else 0
        return []
    if not line.startswith('+') or line.startswith('+++'):
        if line.startswith(' '):
            state.line_number += 1
        return []
    state.line_number += 1
    represented = [
        value for value in (state.old_path, state.new_path) if value
    ]
    if not represented or all(
        is_external_path(value) for value in represented
    ):
        return []
    product_paths = [
        value for value in represented if not is_external_path(value)
    ]
    path = product_paths[0] if product_paths else represented[0]
    return (
        _line_errors(line[1:], path, state.line_number, allowed)
        if _is_text(path)
        else []
    )


def scan_diff(diff: str, allow_print_files: Iterable[str] = ()) -> list[str]:
    """Return violations in added product-owned textual content."""
    allowed = {normalize_path(path) for path in allow_print_files}
    errors: list[str] = []
    state = _DiffState()
    for line in diff.splitlines():
        errors.extend(_scan_diff_line(line, state, allowed))
    return errors
