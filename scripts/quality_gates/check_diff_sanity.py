"""Run the diff-sanity policy against staged or range additions."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from diff_sanity_policy import scan_diff, validate_print_allowlist
from git_changes import (
    GitInspectionError,
    indexed_paths,
    repository_root,
    revision_paths,
    unified_diff,
    validated_revision_range,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the gate with explicit PASS, SKIP, FAIL, and ERROR outcomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--range', dest='revision_range', metavar='BASE...HEAD'
    )
    parser.add_argument(
        '--allow-print-file',
        action='append',
        default=[],
        metavar='PATH',
        help='Allow print() only in this exact repository file.',
    )
    parser.add_argument('files', nargs='*')
    args = parser.parse_args(argv)
    if args.revision_range and args.files:
        print(
            'ERROR [DIFF_SANITY]: --range cannot be combined with paths.',
            file=sys.stderr,
        )
        return 2
    try:
        root = repository_root()
        revision = (
            validated_revision_range(args.revision_range, root)
            if args.revision_range
            else None
        )
        available = (
            revision_paths(root, revision[1])
            if revision is not None
            else indexed_paths(root)
        )
        allowlist_errors = validate_print_allowlist(
            args.allow_print_file, available
        )
        diff = unified_diff(root, args.revision_range, paths=args.files)
    except GitInspectionError as git_error:
        print(f'ERROR [DIFF_SANITY]: {git_error}', file=sys.stderr)
        return 2
    if allowlist_errors:
        print('FAIL [DIFF_SANITY]: Invalid print allowlist:', file=sys.stderr)
        for violation in allowlist_errors:
            print(f'  • {violation}', file=sys.stderr)
        return 1
    if not diff.strip():
        print('SKIP [DIFF_SANITY]: No product additions to inspect.')
        return 0
    errors = scan_diff(diff, args.allow_print_file)
    if errors:
        print(
            'FAIL [DIFF_SANITY]: Unsafe additions detected:', file=sys.stderr
        )
        for violation in errors:
            print(f'  • {violation}', file=sys.stderr)
        return 1
    print('PASS [DIFF_SANITY]: Product additions satisfy the policy.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
