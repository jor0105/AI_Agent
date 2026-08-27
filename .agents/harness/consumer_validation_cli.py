"""Command-line entry point for harness-validate."""

from __future__ import annotations

import argparse
import json
import sys

from harness.consumer_validation import (
    ContractError,
    execute_consumer_validation,
    verify_path_confinement,
)
from harness.paths import GitRootError, strict_repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Validate consumer-owned skills, agents, and workflows.'
    )
    parser.add_argument(
        '--request',
        required=True,
        metavar='PATH',
        help='Repository-relative path to the validation request JSON document.',
    )
    args = parser.parse_args(argv)

    try:
        root = strict_repo_root()
    except GitRootError as exc:
        sys.stderr.write(f'error: {exc}\n')
        return 2

    try:
        request_file = verify_path_confinement(
            root, args.request, 'request path', must_exist=True
        )
    except ContractError as exc:
        sys.stderr.write(f'error: {exc}\n')
        return 2

    try:
        request_data = json.loads(request_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        sys.stderr.write(f'error: cannot read request JSON: {exc}\n')
        return 2

    try:
        result = execute_consumer_validation(root, request_data)
    except ContractError as exc:
        sys.stderr.write(f'error: {exc}\n')
        return 2

    sys.stdout.write(f'{json.dumps(result, indent=2, ensure_ascii=True)}\n')
    if result.get('diagnostics'):
        for diag in result['diagnostics']:
            sys.stderr.write(
                f'[{diag["code"]}] {diag["item"]} ({diag["validatorId"]}): {diag["message"]}\n'
            )
    return int(result.get('exitCode', 0))


if __name__ == '__main__':
    sys.exit(main())
