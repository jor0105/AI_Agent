"""Protect staged tests from silent weakening, skips, and deletion."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from git_index import (
    GitInspectionError,
    read_index_text,
    repository_root,
    staged_diff,
)

STRICT_FOCUS_PATTERNS = (
    (
        re.compile(r'\b(?:it|describe|test)\.only\b'),
        'focused test (.only) is prohibited',
    ),
    (
        re.compile(r'\b(?:fit|fdescribe)\('),
        'focused test (fit/fdescribe) is prohibited',
    ),
)
SKIPPED_TEST_PATTERNS = (
    (
        re.compile(r'@pytest\.mark\.(?:skip|xfail)\b'),
        'skipped/xfailed pytest marker added',
    ),
    (
        re.compile(r'\b(?:it|describe|test)\.skip\b'),
        'skipped test (.skip) added',
    ),
    (re.compile(r'\b(?:xit|xtest)\('), 'skipped test (xit/xtest) added'),
)
ASSERTION_PATTERN = re.compile(
    r'\b(?:assert\s+|expect\(|self\.assert|assert_that\b|t\.assert|'
    r'assertIs|assertEqual|assertTrue|assertFalse)'
)
MIN_REASON_LENGTH = 20
ALLOW_SKIP_RE = re.compile(
    r'(?:allow-skip|skip-reason):\s*(?P<reason>\S.*)', re.IGNORECASE
)
ALLOW_ASSERTION_REDUCTION_RE = re.compile(
    r'(?:allow-assertion-reduction|assertion-reduction-reason):\s*'
    r'(?P<reason>\S.*)',
    re.IGNORECASE,
)
POLICY_PATHS = ('.test-deletions.json', '.test-integrity-policy.json')


def is_test_file(file_path: str) -> bool:
    """Return whether a repository path belongs to a test suite."""
    path = Path(file_path)
    name = path.name.lower()
    posix_path = path.as_posix().lower()
    return (
        name.startswith('test_')
        or name.endswith(
            (
                '_test.py',
                '.test.ts',
                '.test.js',
                '.test.tsx',
                '.test.jsx',
                '.spec.ts',
                '.spec.js',
                '.spec.tsx',
                '.spec.jsx',
            )
        )
        or '/tests/' in posix_path
        or '/__tests__/' in posix_path
        or posix_path.startswith(('tests/', 'test/'))
    )


def _reason_is_present(content: object) -> bool:
    """Return whether a policy reason is a meaningful non-empty string."""
    return (
        isinstance(content, str) and len(content.strip()) >= MIN_REASON_LENGTH
    )


def _has_reason(pattern: re.Pattern[str], content: str) -> bool:
    """Return whether an inline exception carries a reviewable rationale."""
    match = pattern.search(content)
    return match is not None and _reason_is_present(match.group('reason'))


def is_test_deletion_approved(file_path: str, root: Path) -> bool:
    """Return whether the indexed deletion policy explicitly permits a file."""
    for policy_path in POLICY_PATHS:
        content = read_index_text(policy_path, root)
        if content is None:
            continue
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        allowed = payload.get('allowed_deletions')
        if not isinstance(allowed, dict) or file_path not in allowed:
            continue
        reason = allowed[file_path]
        if _reason_is_present(reason):
            return True
        if isinstance(reason, dict) and _reason_is_present(
            reason.get('reason')
        ):
            return True
    return False


def _check_focus_or_skip_line(
    content: str, file_path: str, line_number: int
) -> list[str]:
    """Return strict focus and reasoned skip failures for an added line."""
    errors: list[str] = []
    for pattern, description in STRICT_FOCUS_PATTERNS:
        if pattern.search(content):
            errors.append(
                f'{file_path}:{line_number}: [TEST_FOCUS] {description} '
                f'({content!r})'
            )
    for pattern, description in SKIPPED_TEST_PATTERNS:
        if pattern.search(content) and not _has_reason(ALLOW_SKIP_RE, content):
            errors.append(
                f'{file_path}:{line_number}: [TEST_SKIP] {description} '
                f'without allow-skip: <reason> ({content!r})'
            )
    return errors


@dataclass
class _FileDiffState:
    """Count integrity-relevant changes while scanning one test-file diff."""

    current_file: str = ''
    previous_file: str = ''
    line_number: int = 0
    removed_assertions: int = 0
    added_assertions: int = 0
    has_inline_reduction_reason: bool = False
    is_deleted: bool = False

    def reset(self, file_path: str, *, is_deleted: bool = False) -> None:
        """Start tracking a new changed file."""
        self.current_file = file_path
        self.removed_assertions = 0
        self.added_assertions = 0
        self.has_inline_reduction_reason = False
        self.is_deleted = is_deleted

    def evaluate(self, root: Path, allow_deleted_tests: bool) -> list[str]:
        """Return the accumulated integrity failures for this file."""
        if not self.current_file or not is_test_file(self.current_file):
            return []
        if self.is_deleted:
            if allow_deleted_tests or is_test_deletion_approved(
                self.current_file, root
            ):
                return []
            return [
                f'{self.current_file}: [TEST_DELETION] Test file deleted. '
                'Stage an explicit reason in .test-deletions.json.'
            ]
        if self.removed_assertions <= self.added_assertions:
            return []
        if self.has_inline_reduction_reason:
            return []
        return [
            f'{self.current_file}: [TEST_INTEGRITY] Net assertion reduction '
            f'({self.removed_assertions} removed vs {self.added_assertions} added) '
            'without allow-assertion-reduction: <reason> in the same staged diff.'
        ]


def scan_test_integrity(
    diff_text: str,
    root: Path,
    *,
    allow_deleted_tests: bool = False,
) -> list[str]:
    """Scan a staged diff and return test-integrity violations.

    All auxiliary evidence is loaded through ``read_index_text`` so an
    unstaged file cannot make an unsafe staged commit appear compliant.
    """
    errors: list[str] = []
    state = _FileDiffState()

    for line in diff_text.splitlines():
        if line.startswith('--- a/'):
            state.previous_file = line[6:]
            continue
        if line.startswith('+++ b/'):
            errors.extend(state.evaluate(root, allow_deleted_tests))
            state.reset(line[6:])
            continue
        if line.startswith('+++ /dev/null'):
            errors.extend(state.evaluate(root, allow_deleted_tests))
            state.reset(state.previous_file, is_deleted=True)
            continue
        if not is_test_file(state.current_file):
            continue
        if line.startswith('@@ '):
            match = re.search(r'\+(\d+)', line)
            if match:
                state.line_number = int(match.group(1)) - 1
            continue
        if line.startswith('-') and not line.startswith('---'):
            if ASSERTION_PATTERN.search(line[1:].strip()):
                state.removed_assertions += 1
            continue
        if not line.startswith('+') or line.startswith('+++'):
            continue
        state.line_number += 1
        content = line[1:].strip()
        if not content:
            continue
        if _has_reason(ALLOW_ASSERTION_REDUCTION_RE, content):
            state.has_inline_reduction_reason = True
        if ASSERTION_PATTERN.search(content):
            state.added_assertions += 1
        errors.extend(
            _check_focus_or_skip_line(
                content, state.current_file, state.line_number
            )
        )

    errors.extend(state.evaluate(root, allow_deleted_tests))
    return errors


def main() -> int:
    """Run the staged test-integrity check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*')
    parser.add_argument('--allow-deleted-tests', action='store_true')
    args = parser.parse_args()
    try:
        root = repository_root()
        diff_text = staged_diff(root, args.files, context=1)
        errors = scan_test_integrity(
            diff_text,
            root,
            allow_deleted_tests=args.allow_deleted_tests,
        )
    except GitInspectionError as err:
        print(f'ERROR [TEST_INTEGRITY]: {err}', file=sys.stderr)
        return 2
    if not diff_text.strip():
        print('SKIP [TEST_INTEGRITY]: No staged test changes to inspect.')
        return 0
    if errors:
        print(
            'FAIL [TEST_INTEGRITY]: Staged test changes are unsafe:',
            file=sys.stderr,
        )
        for error in errors:
            print(f'  • {error}', file=sys.stderr)
        print(
            'Resolution: restore the behavior, remove focus/skip markers, or '
            'stage a narrow reason that a reviewer can assess.',
            file=sys.stderr,
        )
        return 1
    print(
        'PASS [TEST_INTEGRITY]: Staged test changes retain their safeguards.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
