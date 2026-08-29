"""Resolve and verify the immutable Git range used by CI quality gates."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from git_changes import GitInspectionError, repository_root, verify_revision

ZERO_SHA = '0' * 40


class CIRangeError(RuntimeError):
    """Raised when CI cannot identify two verifiable commits."""


def _payload_sha(payload: object, *keys: str) -> str:
    value = payload
    for key in keys:
        if not isinstance(value, dict):
            raise CIRangeError(
                f'CI event payload is missing {".".join(keys)}.'
            )
        value = value.get(key)
    if not isinstance(value, str) or not value:
        raise CIRangeError(f'CI event payload has no {".".join(keys)}.')
    return value


def _read_pull_request_range(event_path: Path) -> tuple[str, str]:
    try:
        payload = json.loads(event_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CIRangeError(
            f'could not read the pull-request event: {error}'
        ) from error
    return (
        _payload_sha(payload, 'pull_request', 'base', 'sha'),
        _payload_sha(payload, 'pull_request', 'head', 'sha'),
    )


def _read_push_before(event_path: Path) -> str:
    try:
        payload = json.loads(event_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CIRangeError(
            f'could not read the push event: {error}'
        ) from error
    return _payload_sha(payload, 'before')


def _validate_names(base: str, head: str) -> None:
    if any(
        not value or '\x00' in value or any(char.isspace() for char in value)
        for value in (base, head)
    ):
        raise CIRangeError('CI range contains an invalid revision name.')


def resolve_range(
    event_name: str | None,
    event_path: Path | None,
    before: str | None,
    sha: str | None,
    root: Path,
    *,
    base: str | None = None,
    head: str | None = None,
) -> str:
    """Return a verified ``BASE...HEAD`` expression for a CI event."""
    if (base is None) != (head is None):
        raise CIRangeError('--base and --head must be supplied together.')
    if base is not None and head is not None:
        selected_base, selected_head = base, head
    elif event_name == 'pull_request':
        if event_path is None:
            raise CIRangeError(
                'pull-request validation requires GITHUB_EVENT_PATH.'
            )
        selected_base, selected_head = _read_pull_request_range(event_path)
    elif event_name == 'push':
        push_before = before
        if push_before is None and event_path is not None:
            try:
                push_before = _read_push_before(event_path)
            except CIRangeError:
                push_before = None
        if push_before and sha and push_before != ZERO_SHA and sha != ZERO_SHA:
            selected_base, selected_head = push_before, sha
        else:
            selected_base, selected_head = 'HEAD^', 'HEAD'
    else:
        selected_base, selected_head = 'HEAD^', 'HEAD'
    _validate_names(selected_base, selected_head)
    return (
        f'{verify_revision(selected_base, root)}...'
        f'{verify_revision(selected_head, root)}'
    )


def main(argv: list[str] | None = None) -> int:
    """Print a verified CI range or fail closed with exit code 2."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base')
    parser.add_argument('--head')
    parser.add_argument(
        '--event-name', default=os.environ.get('GITHUB_EVENT_NAME')
    )
    parser.add_argument(
        '--event-path',
        type=Path,
        default=os.environ.get('GITHUB_EVENT_PATH'),
    )
    parser.add_argument(
        '--before', default=os.environ.get('GITHUB_EVENT_BEFORE')
    )
    parser.add_argument('--sha', default=os.environ.get('GITHUB_SHA'))
    args = parser.parse_args(argv)
    event_path = None if args.event_path is None else Path(args.event_path)
    try:
        result = resolve_range(
            args.event_name,
            event_path,
            args.before,
            args.sha,
            repository_root(),
            base=args.base,
            head=args.head,
        )
        print(result)
    except (CIRangeError, GitInspectionError) as error:
        print(f'ERROR [CI_RANGE]: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
