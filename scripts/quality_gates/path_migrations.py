"""Identify path-only migrations in unified diffs."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseOnlyTestRename:
    """Describe the added side of a case-only test path migration."""

    added_assertions: int
    has_assertion_reduction_reason: bool


def _section_path(section: str, prefix: str) -> str | None:
    """Extract a path from a unified-diff file header."""
    match = re.search(
        rf'^{re.escape(prefix)}(.+)$', section, flags=re.MULTILINE
    )
    if match is None:
        return None
    return match.group(1).split('\t', 1)[0]


def _added_lines(section: str) -> list[str]:
    """Return content lines added by a unified-diff section."""
    return [
        line[1:].strip()
        for line in section.splitlines()
        if line.startswith('+') and not line.startswith('+++')
    ]


def find_case_only_test_renames(
    diff_text: str,
    *,
    is_test_file: Callable[[str], bool],
    assertion_pattern: re.Pattern[str],
    reduction_reason_pattern: re.Pattern[str],
) -> dict[str, CaseOnlyTestRename]:
    """Return deleted test paths replaced with the same path casing-folded."""
    deleted: dict[str, list[str]] = {}
    added: dict[str, list[tuple[str, CaseOnlyTestRename]]] = {}
    sections = re.split(r'(?=^diff --git )', diff_text, flags=re.MULTILINE)
    for section in sections:
        old_path = _section_path(section, '--- a/')
        new_path = _section_path(section, '+++ b/')
        if (
            '+++ /dev/null' in section
            and old_path is not None
            and is_test_file(old_path)
        ):
            deleted.setdefault(old_path.casefold(), []).append(old_path)
        if (
            '--- /dev/null' in section
            and new_path is not None
            and is_test_file(new_path)
        ):
            lines = _added_lines(section)
            added.setdefault(new_path.casefold(), []).append(
                (
                    new_path,
                    CaseOnlyTestRename(
                        added_assertions=sum(
                            assertion_pattern.search(line) is not None
                            for line in lines
                        ),
                        has_assertion_reduction_reason=any(
                            reduction_reason_pattern.search(line) is not None
                            for line in lines
                        ),
                    ),
                )
            )

    migrations: dict[str, CaseOnlyTestRename] = {}
    for folded_path, old_paths in deleted.items():
        new_paths = added.get(folded_path, [])
        if len(old_paths) != 1 or len(new_paths) != 1:
            continue
        old_path = old_paths[0]
        new_path, migration = new_paths[0]
        if old_path != new_path:
            migrations[old_path] = migration
    return migrations
