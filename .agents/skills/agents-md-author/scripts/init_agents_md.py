#!/usr/bin/env python3
"""Create a portable AGENTS.md scaffold without overwriting existing files."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime
from pathlib import Path

TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1] / 'assets' / 'AGENTS.template.md'
)


def _single_line(value: str) -> str:
    normalized = value.strip()
    if not normalized or '\n' in value or '\r' in value:
        raise argparse.ArgumentTypeError(
            'value must be a non-empty single line'
        )
    return normalized


def render_template(*, owner: str, status: str, reviewed: str) -> str:
    """Render deterministic metadata into the bundled template."""
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    return (
        template.replace('> Owner: Unassigned', f'> Owner: {owner}', 1)
        .replace(
            '> Last reviewed: YYYY-MM-DD', f'> Last reviewed: {reviewed}', 1
        )
        .replace('> Status: Draft', f'> Status: {status}', 1)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Create an AGENTS.md scaffold from the portable template.'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('AGENTS.md'),
        help='Destination path (default: AGENTS.md)',
    )
    parser.add_argument(
        '--owner',
        type=_single_line,
        default='Unassigned',
        help='Confirmed owner or Unassigned (default: Unassigned)',
    )
    parser.add_argument(
        '--status',
        type=_single_line,
        default='Draft',
        help='Confirmed document status (default: Draft)',
    )
    parser.add_argument(
        '--reviewed',
        default=datetime.now(tz=UTC).date().isoformat(),
        help='Review date in YYYY-MM-DD format (default: today)',
    )
    parser.add_argument(
        '--stdout',
        action='store_true',
        help='Print the scaffold instead of writing a file.',
    )
    args = parser.parse_args()

    try:
        date.fromisoformat(args.reviewed)
    except ValueError:
        print('ERROR: --reviewed must use YYYY-MM-DD.', file=sys.stderr)
        return 2

    try:
        rendered = render_template(
            owner=args.owner,
            status=args.status,
            reviewed=args.reviewed,
        )
    except OSError as exc:
        print(f'ERROR: cannot read bundled template: {exc}', file=sys.stderr)
        return 2

    if args.stdout:
        print(rendered, end='')
        return 0

    if not args.output.parent.is_dir():
        print(
            f'ERROR: destination parent does not exist: {args.output.parent}',
            file=sys.stderr,
        )
        return 2

    try:
        with args.output.open('x', encoding='utf-8', newline='\n') as output:
            output.write(rendered)
    except FileExistsError:
        print(
            f'ERROR: destination already exists: {args.output}',
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(f'ERROR: cannot write {args.output}: {exc}', file=sys.stderr)
        return 2

    print(f'CREATED: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
