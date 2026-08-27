"""Discovery and selection for consumer validation scopes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.consumer_validators import (
    Diagnostic,
    validate_agent_item,
    validate_skill_item,
    validate_workflow_item,
)

SKIP_PARTS = {
    '__pycache__',
    '.git',
    'references',
    'assets',
    'scripts',
    'templates',
    'schemas',
    'data',
}


@dataclass(frozen=True)
class DiscoveredItem:
    name: str
    path: str
    file_path: Path
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            'name': self.name,
            'path': self.path,
            'sha256': self.sha256,
        }

    def validate(self, root: Path, scope_name: str) -> list[Diagnostic]:
        if scope_name == 'skills':
            return validate_skill_item(
                root, self.file_path, self.path, self.name
            )
        if scope_name == 'agents':
            return validate_agent_item(
                root, self.file_path, self.path, self.name
            )
        if scope_name == 'workflows':
            return validate_workflow_item(
                root, self.file_path, self.path, self.name
            )
        return []


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def discover_scope_items(
    root: Path, scope_name: str, scope_path_str: str
) -> list[DiscoveredItem]:
    scope_dir = root / scope_path_str
    if not scope_dir.exists():
        return []
    items: list[DiscoveredItem] = []
    if scope_name == 'skills':
        for skill_file in sorted(scope_dir.rglob('SKILL.md')):
            parts = skill_file.relative_to(scope_dir).parts
            if any(p in SKIP_PARTS for p in parts[:-1]):
                continue
            name = skill_file.relative_to(scope_dir).parent.as_posix()
            rel = skill_file.relative_to(root).as_posix()
            items.append(
                DiscoveredItem(
                    name=name,
                    path=rel,
                    file_path=skill_file,
                    sha256=_sha256_bytes(skill_file.read_bytes()),
                )
            )
    elif scope_name == 'agents':
        for agent_file in sorted(scope_dir.rglob('*.agent.md')):
            if any(
                p in SKIP_PARTS
                for p in agent_file.relative_to(scope_dir).parts[:-1]
            ):
                continue
            name = agent_file.relative_to(scope_dir).as_posix()
            rel = agent_file.relative_to(root).as_posix()
            items.append(
                DiscoveredItem(
                    name=name,
                    path=rel,
                    file_path=agent_file,
                    sha256=_sha256_bytes(agent_file.read_bytes()),
                )
            )
    elif scope_name == 'workflows':
        for wf_file in sorted(scope_dir.rglob('*.prompt.md')):
            if any(
                p in SKIP_PARTS
                for p in wf_file.relative_to(scope_dir).parts[:-1]
            ):
                continue
            name = wf_file.relative_to(scope_dir).as_posix()
            rel = wf_file.relative_to(root).as_posix()
            items.append(
                DiscoveredItem(
                    name=name,
                    path=rel,
                    file_path=wf_file,
                    sha256=_sha256_bytes(wf_file.read_bytes()),
                )
            )
    return items


def apply_scope_selection(
    scope_name: str, scope_def: dict[str, Any], discovered: list[DiscoveredItem]
) -> tuple[list[DiscoveredItem], list[DiscoveredItem]]:
    is_required = scope_def['required']
    include = scope_def.get('include', [])
    exclude = scope_def.get('exclude', [])
    if is_required:
        if include or exclude:
            raise ValueError(
                f"required scope '{scope_name}' cannot use include or exclude filters"
            )
        return list(discovered), []
    if len(include) != len(set(include)):
        raise ValueError(
            f"duplicate names in include filter for scope '{scope_name}'"
        )
    if len(exclude) != len(set(exclude)):
        raise ValueError(
            f"duplicate names in exclude filter for scope '{scope_name}'"
        )
    overlap = set(include) & set(exclude)
    if overlap:
        raise ValueError(
            f"overlapping names in include/exclude for scope '{scope_name}': {sorted(overlap)}"
        )
    disc_map = {item.name: item for item in discovered}
    for name in include:
        if name not in disc_map:
            raise ValueError(
                f"unmatched include filter name '{name}' in scope '{scope_name}'"
            )
    for name in exclude:
        if name not in disc_map:
            raise ValueError(
                f"unmatched exclude filter name '{name}' in scope '{scope_name}'"
            )
    effective_names = (
        set(include) if include else set(disc_map.keys())
    ) - set(exclude)
    if (include or exclude) and not effective_names:
        raise ValueError(
            f"filtering for scope '{scope_name}' produces an empty selection"
        )
    effective = [disc_map[n] for n in sorted(effective_names)]
    excluded = [item for item in discovered if item.name not in effective_names]
    return effective, excluded
