"""Fail closed when staged hook configuration weakens local quality gates."""

from __future__ import annotations

import sys

from git_index import (
    GitInspectionError,
    read_index_text,
    repository_root,
    staged_changes,
)
from hook_policy import PRE_COMMIT_PATH, _validate_pre_commit_config

RELEVANT_PATHS = frozenset(
    {
        PRE_COMMIT_PATH,
        'scripts/quality_gates/hook_config.py',
        'scripts/quality_gates/hook_policy.py',
        'scripts/quality_gates/quality_gate_policy.py',
    }
)


def validate_quality_gate_config(pre_commit_text: str) -> list[str]:
    """Return violations in the staged pre-commit configuration."""
    return _validate_pre_commit_config(pre_commit_text)


def main() -> int:
    """Run policy validation only when policy-related files are staged."""
    try:
        root = repository_root()
        changed_paths = {change.new_path for change in staged_changes(root)}
        if not changed_paths & RELEVANT_PATHS:
            print('SKIP [QUALITY_GATE_POLICY]: No policy files staged.')
            return 0
        pre_commit_text = read_index_text(PRE_COMMIT_PATH, root)
    except GitInspectionError as err:
        print(f'ERROR [QUALITY_GATE_POLICY]: {err}', file=sys.stderr)
        return 2
    if pre_commit_text is None:
        print(
            'FAIL [QUALITY_GATE_POLICY]: .pre-commit-config.yaml is absent from the index.',
            file=sys.stderr,
        )
        return 1
    errors = validate_quality_gate_config(pre_commit_text)
    if errors:
        print(
            'FAIL [QUALITY_GATE_POLICY]: Local gate policy was weakened:',
            file=sys.stderr,
        )
        for error in errors:
            print(f'  • {error}', file=sys.stderr)
        return 1
    print('PASS [QUALITY_GATE_POLICY]: Staged quality-gate policy is intact.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
