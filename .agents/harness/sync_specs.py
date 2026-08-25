#!/usr/bin/env python3
"""Deterministically apply OpenSpec delta operations to canonical specs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from harness.paths import repo_root as current_repo_root

OPERATION_RE = re.compile(
    r'^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+Requirements\s*$', re.I
)
REQUIREMENT_RE = re.compile(r'^###\s+Requirement:\s*(.+?)\s*$')
PURPOSE_RE = re.compile(r'^##\s+Purpose\s*$', re.I)
REQUIREMENTS_RE = re.compile(r'^##\s+Requirements\s*$', re.I)
RENAME_RE = re.compile(
    r'^-\s+(FROM|TO):\s+`?(?:###\s+Requirement:\s*)?(.+?)`?\s*$', re.I
)
PLACEHOLDER_RE = re.compile(r'\b(?:TBD|TODO|FIXME|XXX)\b|<[^>]+>', re.I)
DECISION_SOURCE_RE = re.compile(
    r'^[ \t]*Decision source:[ \t]*(.+?)[ \t]*$', re.MULTILINE
)


@dataclass(frozen=True)
class RequirementBlock:
    name: str
    text: str


@dataclass(frozen=True)
class DeltaSpec:
    purpose: str
    added: tuple[RequirementBlock, ...]
    modified: tuple[RequirementBlock, ...]
    removed: tuple[str, ...]
    renamed: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SyncIssue:
    capability: str
    code: str
    message: str


def _normalize_block(lines: list[str]) -> str:
    cleaned = [line.rstrip() for line in lines]
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return '\n'.join(cleaned)


def _section_body(lines: list[str], heading: re.Pattern[str]) -> str:
    start: int | None = None
    for index, line in enumerate(lines):
        if heading.match(line):
            start = index + 1
            break
    if start is None:
        return ''
    end = next(
        (
            index
            for index in range(start, len(lines))
            if lines[index].startswith('## ')
        ),
        len(lines),
    )
    return _normalize_block(lines[start:end]).strip()


def _requirement_blocks(lines: list[str]) -> tuple[RequirementBlock, ...]:
    starts = [
        (index, match.group(1).strip())
        for index, line in enumerate(lines)
        if (match := REQUIREMENT_RE.match(line))
    ]
    result: list[RequirementBlock] = []
    for position, (start, name) in enumerate(starts):
        end = (
            starts[position + 1][0]
            if position + 1 < len(starts)
            else len(lines)
        )
        result.append(
            RequirementBlock(name, _normalize_block(lines[start:end]))
        )
    return tuple(result)


def parse_delta(text: str) -> DeltaSpec:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = OPERATION_RE.match(line)
        if match:
            current = match.group(1).lower()
            sections[current] = []
        elif current is not None:
            if line.startswith('## '):
                current = None
            else:
                sections[current].append(line)
    rename_pairs: list[tuple[str, str]] = []
    pending_from: str | None = None
    for line in sections.get('renamed', []):
        if match := RENAME_RE.match(line):
            side = match.group(1).lower()
            value = match.group(2).strip()
            if side == 'from':
                if pending_from is not None:
                    raise ValueError(
                        'RENAMED contains a FROM without a matching TO'
                    )
                pending_from = value
            elif pending_from is None:
                raise ValueError(
                    'RENAMED contains a TO without a matching FROM'
                )
            else:
                rename_pairs.append((pending_from, value))
                pending_from = None
    if pending_from is not None:
        raise ValueError('RENAMED contains a FROM without a matching TO')
    return DeltaSpec(
        purpose=_section_body(lines, PURPOSE_RE),
        added=_requirement_blocks(sections.get('added', [])),
        modified=_requirement_blocks(sections.get('modified', [])),
        removed=tuple(
            block.name
            for block in _requirement_blocks(sections.get('removed', []))
        ),
        renamed=tuple(rename_pairs),
    )


def _main_parts(text: str) -> tuple[str, list[RequirementBlock]]:
    lines = text.splitlines()
    heading = next(
        (
            index
            for index, line in enumerate(lines)
            if REQUIREMENTS_RE.match(line)
        ),
        None,
    )
    if heading is None:
        raise ValueError('canonical spec has no ## Requirements section')
    starts = [
        index
        for index in range(heading + 1, len(lines))
        if REQUIREMENT_RE.match(lines[index])
    ]
    first = starts[0] if starts else len(lines)
    prefix = _normalize_block(lines[:first])
    return prefix, list(_requirement_blocks(lines[first:]))


def _load_opsx(repo_root: Path) -> ModuleType:
    module_path = Path(__file__).with_name('opsx.py')
    spec = importlib.util.spec_from_file_location(
        f'opsx_sync_preflight_{id(repo_root)}', module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load decision preflight: {module_path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    opsx_module = cast(Any, module)
    opsx_module.REPO_ROOT = repo_root
    opsx_module.CHANGES_ROOT = repo_root / 'openspec/changes'
    return module


def _decision_preflight(
    repo_root: Path, change_name: str
) -> tuple[tuple[str, ...], list[SyncIssue]]:
    try:
        opsx = _load_opsx(repo_root)
        source, findings = opsx.validate_decision_source(
            repo_root / 'openspec/changes' / change_name
        )
    except (OSError, RuntimeError, ValueError) as exc:
        return (), [SyncIssue('manifest', 'sync-provenance-error', str(exc))]
    if findings:
        return (), [
            SyncIssue(
                'manifest',
                'sync-provenance-error',
                f'{item["code"]}: {item["message"]}',
            )
            for item in findings
        ]
    if source is None:
        return (), [
            SyncIssue(
                'manifest',
                'sync-provenance-error',
                'decision-source preflight returned no source envelope',
            )
        ]
    raw_ids = source.get('decision_ids')
    if not isinstance(raw_ids, list) or not all(
        isinstance(item, str) for item in raw_ids
    ):
        return (), [
            SyncIssue(
                'manifest',
                'sync-provenance-error',
                'decision-source preflight returned invalid decision IDs',
            )
        ]
    return tuple(raw_ids), []


def _with_provenance(prefix: str, decision_ids: tuple[str, ...]) -> str:
    lines = prefix.splitlines()
    heading = next(
        i for i, line in enumerate(lines) if REQUIREMENTS_RE.match(line)
    )
    prefix_text = '\n'.join(lines[:heading])
    existing_ids = DECISION_SOURCE_RE.findall(prefix_text)
    source_ids = set(re.findall(r'Q\d+', ','.join(existing_ids)))
    merged_ids = sorted(
        source_ids | set(decision_ids), key=lambda item: int(item[1:])
    )
    clean_prefix = (
        DECISION_SOURCE_RE.sub('', prefix_text).rstrip().splitlines()
    )
    provenance = [f'Decision source: {item}' for item in merged_ids]
    return _normalize_block(
        [
            *clean_prefix,
            '',
            *provenance,
            '',
            *lines[heading:],
        ]
    )


def _new_prefix(
    capability: str, delta: DeltaSpec, decision_ids: tuple[str, ...]
) -> str:
    if not delta.purpose or PLACEHOLDER_RE.search(delta.purpose):
        raise ValueError('new capability requires a concrete delta Purpose')
    title = capability.replace('-', ' ').title()
    provenance = '\n'.join(f'Decision source: {item}' for item in decision_ids)
    return (
        f'# {title}\n\n## Purpose\n\n{delta.purpose}\n\n'
        f'{provenance}\n\n## Requirements'
    )


def _find_requirement_index(
    blocks: list[RequirementBlock], name: str
) -> int | None:
    exact = next(
        (index for index, block in enumerate(blocks) if block.name == name),
        None,
    )
    if exact is not None:
        return exact
    clean_name = name.replace('`', '')
    no_ticks = next(
        (
            index
            for index, block in enumerate(blocks)
            if block.name.replace('`', '') == clean_name
        ),
        None,
    )
    if no_ticks is not None:
        return no_ticks
    for keyword in (' SHALL ', ' MUST '):
        if keyword in name:
            suffix = name.split(keyword, 1)[1]
            matches = [
                index
                for index, block in enumerate(blocks)
                if keyword in block.name
                and block.name.split(keyword, 1)[1] == suffix
            ]
            if len(matches) == 1:
                return matches[0]
    return None


def _apply_renames(
    blocks: list[RequirementBlock], renamed: tuple[tuple[str, str], ...]
) -> None:
    for old, new in renamed:
        old_index = _find_requirement_index(blocks, old)
        new_index = _find_requirement_index(blocks, new)
        if old_index is None and new_index is not None:
            continue
        if old_index is None:
            raise ValueError(f'RENAMED source requirement is absent: {old}')
        if new_index is not None:
            raise ValueError(
                f'RENAMED target requirement already exists: {new}'
            )
        old_block = blocks[old_index]
        renamed_text = old_block.text.replace(
            f'### Requirement: {old}', f'### Requirement: {new}', 1
        )
        blocks[old_index] = RequirementBlock(new, renamed_text)


def render_sync(
    capability: str,
    delta: DeltaSpec,
    current: str | None,
    decision_ids: tuple[str, ...],
) -> str:
    if current is None:
        prefix = _new_prefix(capability, delta, decision_ids)
        blocks: list[RequirementBlock] = []
    else:
        prefix, blocks = _main_parts(current)
        purpose = _section_body(current.splitlines(), PURPOSE_RE)
        if not purpose or PLACEHOLDER_RE.search(purpose):
            raise ValueError('canonical spec Purpose is missing or unresolved')
        prefix = _with_provenance(prefix, decision_ids)

    for block in delta.added:
        index = _find_requirement_index(blocks, block.name)
        if index is None:
            blocks.append(block)
        elif blocks[index].text != block.text:
            raise ValueError(
                f'ADDED requirement already exists with different content: {block.name}'
            )
    for block in delta.modified:
        index = _find_requirement_index(blocks, block.name)
        if index is None:
            raise ValueError(f'MODIFIED requirement is absent: {block.name}')
        blocks[index] = block
    for name in delta.removed:
        index = _find_requirement_index(blocks, name)
        if index is not None:
            blocks.pop(index)
    _apply_renames(blocks, delta.renamed)
    body = '\n\n'.join(block.text for block in blocks)
    return f'{prefix.rstrip()}\n\n{body}\n' if body else f'{prefix.rstrip()}\n'


def sync_change(
    repo_root: Path, change_name: str, *, write: bool
) -> tuple[list[dict[str, object]], list[SyncIssue]]:
    change_root = repo_root / 'openspec/changes' / change_name
    decision_ids, issues = _decision_preflight(repo_root, change_name)
    operations: list[dict[str, object]] = []
    if issues:
        return operations, issues
    planned: list[tuple[Path, str, bool]] = []
    for delta_path in sorted((change_root / 'specs').glob('*/spec.md')):
        capability = delta_path.parent.name
        main_path = repo_root / 'openspec/specs' / capability / 'spec.md'
        try:
            delta = parse_delta(delta_path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            issues.append(
                SyncIssue(capability, 'sync-contract-error', str(exc))
            )
            continue
        current = (
            main_path.read_text(encoding='utf-8')
            if main_path.is_file()
            else None
        )
        try:
            expected = render_sync(capability, delta, current, decision_ids)
        except ValueError as exc:
            issues.append(
                SyncIssue(capability, 'sync-contract-error', str(exc))
            )
            continue
        changed = current != expected
        operations.append(
            {
                'capability': capability,
                'changed': changed,
                'added': [item.name for item in delta.added],
                'modified': [item.name for item in delta.modified],
                'removed': list(delta.removed),
                'renamed': [list(item) for item in delta.renamed],
            }
        )
        planned.append((main_path, expected, changed))
    if issues:
        return operations, issues
    if write:
        for main_path, expected, changed in planned:
            if changed:
                main_path.parent.mkdir(parents=True, exist_ok=True)
                main_path.write_text(expected, encoding='utf-8')
    else:
        for operation, (_, _, changed) in zip(
            operations, planned, strict=True
        ):
            if changed:
                capability = str(operation['capability'])
                main_path = (
                    repo_root / 'openspec/specs' / capability / 'spec.md'
                )
                issues.append(
                    SyncIssue(
                        capability,
                        'delta-unsynchronized',
                        f'{main_path.relative_to(repo_root)} differs from deterministic delta result.',
                    )
                )
    return operations, issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--change', required=True)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--repo-root', type=Path)
    parser.add_argument('--json', action='store_true')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root or current_repo_root()
    operations, issues = sync_change(
        repo_root.resolve(), args.change, write=not args.check
    )
    payload = {
        'changeName': args.change,
        'mode': 'check' if args.check else 'write',
        'operations': operations,
        'findings': [item.__dict__ for item in issues],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
